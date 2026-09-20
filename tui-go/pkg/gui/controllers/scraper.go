package controllers

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"

	"avdc-tui/pkg/gui/helpers"
	"avdc-tui/pkg/python"
)

// ScrapingState tracks the current scraping progress.
type ScrapingState struct {
	Running bool
	Total   int
	Success int
	Failed  int
	Current int
	Dir     string
	mu      sync.Mutex
}

// IsRunning returns true if scraping is in progress.
func (s *ScrapingState) IsRunning() bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.Running
}

// SetRunning sets the running flag.
func (s *ScrapingState) SetRunning(r bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Running = r
}

// IncrementSuccess increments the success counter.
func (s *ScrapingState) IncrementSuccess() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Success++
}

// IncrementFailed increments the failed counter.
func (s *ScrapingState) IncrementFailed() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Failed++
}

// UpdateProgress updates current progress values.
func (s *ScrapingState) UpdateProgress(current, total int) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Current = current
	s.Total = total
}

// JSONEvent represents a JSON line from cli.py --json-output.
type JSONEvent struct {
	Type    string `json:"type"`
	Msg     string `json:"msg,omitempty"`
	File    string `json:"file,omitempty"`
	Suffix  string `json:"suffix,omitempty"`
	Reason  string `json:"reason,omitempty"`
	Error   string `json:"error,omitempty"`
	Current int    `json:"current,omitempty"`
	Total   int    `json:"total,omitempty"`
	Success int    `json:"success,omitempty"`
	Failed  int    `json:"failed,omitempty"`
	Result  string `json:"result,omitempty"`
}

// Scraper manages subprocess calls to cli.py.
type Scraper struct {
	gui    GUI
	state  *ScrapingState
	client *python.Client
}

// NewScraper creates a new scraper.
func NewScraper(g GUI, client *python.Client) *Scraper {
	return &Scraper{
		gui:    g,
		state:  &ScrapingState{},
		client: client,
	}
}

// GetState returns the current scraping state.
func (s *Scraper) GetState() *ScrapingState {
	return s.state
}

// StartScrape launches cli.py as a subprocess and streams JSON output.
func (s *Scraper) StartScrape(dir string, mode int) error {
	if s.state.IsRunning() {
		return fmt.Errorf("scrape already in progress")
	}

	s.state.SetRunning(true)
	s.state.Dir = dir
	s.state.Total = 0
	s.state.Success = 0
	s.state.Failed = 0
	s.state.Current = 0

	s.gui.ClearResults()
	s.gui.AppendLog("Starting scrape: mode="+fmt.Sprint(mode)+" dir="+dir, helpers.LevelInfo)

	go s.runScrape(dir, mode)
	return nil
}

func (s *Scraper) runScrape(dir string, mode int) {
	defer s.state.SetRunning(false)

	if s.client == nil {
		s.gui.AppendLog("Error: Python client not initialized", helpers.LevelError)
		return
	}

	projectRoot := s.client.ProjectRoot()
	if projectRoot == "" {
		s.gui.AppendLog("Error: cannot find project root", helpers.LevelError)
		return
	}

	cmd := exec.Command(
		"uv", "run", "python",
		filepath.Join(projectRoot, "cli", "cli.py"),
		"--path", dir,
		"--main-mode", fmt.Sprint(mode),
		"--json-output",
	)
	cmd.Dir = projectRoot

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		s.gui.AppendLog("Error creating stdout pipe: "+err.Error(), helpers.LevelError)
		return
	}

	stderr, _ := cmd.StderrPipe()

	if err := cmd.Start(); err != nil {
		s.gui.AppendLog("Error starting cli.py: "+err.Error(), helpers.LevelError)
		return
	}

	// Read stdout JSON lines
	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Text()
		s.handleJSONLine(line)
	}

	// Read stderr for any non-JSON output
	errScanner := bufio.NewScanner(stderr)
	for errScanner.Scan() {
		line := errScanner.Text()
		if strings.TrimSpace(line) != "" {
			s.gui.AppendLog("[STDERR] "+line, helpers.LevelInfo)
		}
	}

	if err := cmd.Wait(); err != nil {
		s.gui.AppendLog("Process exited with error: "+err.Error(), helpers.LevelError)
	}

	s.gui.AppendLog(
		fmt.Sprintf("Done: %d total, %d success, %d failed",
			s.state.Total, s.state.Success, s.state.Failed),
		0,
	)

	s.gui.UpdateStatusDone(s.state.Success, s.state.Failed, s.state.Total, dir)
}

func (s *Scraper) handleJSONLine(line string) {
	var event JSONEvent
	if err := json.Unmarshal([]byte(line), &event); err != nil {
		s.gui.AppendLog("Parse error: "+err.Error(), helpers.LevelError)
		return
	}

	switch event.Type {
	case "log":
		s.gui.AppendLog(event.Msg, helpers.LevelInfo)

	case "progress":
		s.state.UpdateProgress(event.Current, event.Total)
		s.gui.UpdateStatusScraping(event.Current, event.Total, s.state.Dir)
		s.gui.AppendLog(fmt.Sprintf("[%d/%d] %s", event.Current, event.Total, event.File), helpers.LevelInfo)

	case "success":
		s.state.IncrementSuccess()
		fileName := filepath.Base(event.File)
		s.gui.AddResult(fmt.Sprintf("[OK] %s %s", fileName, event.Suffix), helpers.LevelInfo)

	case "failure":
		s.state.IncrementFailed()
		fileName := filepath.Base(event.File)
		s.gui.AddResult(fmt.Sprintf("[FAIL] %s: %s", fileName, event.Reason), helpers.LevelError)
		s.gui.AppendLog(fmt.Sprintf("[FAIL] %s: %s", fileName, event.Reason), helpers.LevelError)

	case "done":
		s.state.Total = event.Total
		s.state.Success = event.Success
		s.state.Failed = event.Failed
	}
}

