package controllers

import (
	"fmt"
	"path/filepath"
	"sync"

	"avdc-tui/pkg/commands"
	"avdc-tui/pkg/gui/helpers"
	"avdc-tui/pkg/python"
)

// ScrapingState tracks the current scraping progress.
type ScrapingState struct {
	Running    bool
	Cancelling bool
	Total      int
	Success    int
	Failed     int
	Current    int
	Dir        string
	mu         sync.Mutex
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

// IsCancelling returns true if a cancel was requested.
func (s *ScrapingState) IsCancelling() bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.Cancelling
}

// SetCancelling sets the cancelling flag.
func (s *ScrapingState) SetCancelling(c bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Cancelling = c
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

// Scraper 管理刮削子进程：通过 commands.ProcessRunner
// 流式解析 JSONL 事件并更新状态/视图。
type Scraper struct {
	gui    GUI
	state  *ScrapingState
	runner *commands.ProcessRunner
}

// NewScraper creates a new scraper with a ProcessRunner
// pointed at cli/cli.py.
func NewScraper(g GUI) *Scraper {
	projectRoot := python.FindProjectRoot()
	cliPath := filepath.Join(projectRoot, "cli", "cli.py")
	return &Scraper{
		gui:    g,
		state:  &ScrapingState{},
		runner: commands.NewProcessRunner(projectRoot, cliPath),
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
	s.state.SetCancelling(false)
	s.state.Dir = dir
	s.state.Total = 0
	s.state.Success = 0
	s.state.Failed = 0
	s.state.Current = 0

	s.gui.ClearResults()
	s.gui.AppendLog("Starting scrape: mode="+fmt.Sprint(mode)+
		" dir="+dir, helpers.LevelInfo)

	go s.runScrape(dir, mode)
	return nil
}

func (s *Scraper) runScrape(dir string, mode int) {
	defer s.state.SetRunning(false)

	args := commands.ProcessArgs(dir, mode)
	err := s.runner.Run(args, s.handleEvent, func(line string) {
		s.gui.AppendLog("[STDERR] "+line, helpers.LevelInfo)
	})

	if s.state.IsCancelling() {
		s.gui.AppendLog("Scrape cancelled", helpers.LevelInfo)
		s.state.SetCancelling(false)
		return
	}
	if err != nil {
		s.gui.AppendLog("Process error: "+err.Error(), helpers.LevelError)
	}

	s.gui.AppendLog(
		fmt.Sprintf("Done: %d total, %d success, %d failed",
			s.state.Total, s.state.Success, s.state.Failed),
		helpers.LevelInfo,
	)
	s.gui.UpdateStatusDone(s.state.Success, s.state.Failed,
		s.state.Total, dir)
}

// handleEvent 处理一条 JSONL 事件，更新状态与视图。
func (s *Scraper) handleEvent(ev commands.Event) {
	switch ev.Type {
	case "log":
		s.gui.AppendLog(ev.Msg, helpers.LevelInfo)

	case "progress":
		s.state.UpdateProgress(ev.Current, ev.Total)
		s.gui.UpdateStatusScraping(ev.Current, ev.Total, s.state.Dir)
		s.gui.AppendLog(fmt.Sprintf("[%d/%d] %s",
			ev.Current, ev.Total, ev.File), helpers.LevelInfo)

	case "success":
		s.state.IncrementSuccess()
		fileName := filepath.Base(ev.File)
		s.gui.AddResult(fmt.Sprintf("[OK] %s %s",
			fileName, ev.Suffix), helpers.LevelInfo)

	case "failure":
		s.state.IncrementFailed()
		fileName := filepath.Base(ev.File)
		s.gui.AddResult(fmt.Sprintf("[FAIL] %s: %s",
			fileName, ev.Reason), helpers.LevelError)
		s.gui.AppendLog(fmt.Sprintf("[FAIL] %s: %s",
			fileName, ev.Reason), helpers.LevelError)

	case "done":
		s.state.Total = ev.Total
		s.state.Success = ev.Success
		s.state.Failed = ev.Failed
	}
}

// Cancel 取消当前刮削任务（kill 进程组，不残留子进程）。
// 未运行时无操作。
func (s *Scraper) Cancel() {
	if !s.state.IsRunning() {
		return
	}
	s.state.SetCancelling(true)
	s.runner.Cancel()
}
