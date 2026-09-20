package controllers

import (
	"testing"

	"avdc-tui/pkg/commands"
	"avdc-tui/pkg/gui/types"

	"github.com/jesseduffield/gocui"
)

// mockGUIForScraper is a minimal mock for scraper testing.
type mockGUIForScraper struct {
	logs     []string
	logCs    []gocui.Attribute
	results  []string
	resultCs []gocui.Attribute
}

func (m *mockGUIForScraper) SetView(name string) error                            { return nil }
func (m *mockGUIForScraper) GetView(name string) (*gocui.View, error)             { return nil, nil }
func (m *mockGUIForScraper) SetViewTitle(v *gocui.View, title string)             {}
func (m *mockGUIForScraper) GetScanDir() string                                   { return "" }
func (m *mockGUIForScraper) SetScanDir(dir string)                                {}
func (m *mockGUIForScraper) SetFileList(files []types.VideoFile)                   {}
func (m *mockGUIForScraper) UpdateStatusReady(dir string, count int)              {}
func (m *mockGUIForScraper) UpdateStatusScraping(c, t int, d string)              {}
func (m *mockGUIForScraper) UpdateStatusDone(s, f, t int, d string)               {}
func (m *mockGUIForScraper) AppendLog(msg string, color gocui.Attribute) error {
	m.logs = append(m.logs, msg)
	m.logCs = append(m.logCs, color)
	return nil
}
func (m *mockGUIForScraper) AddResult(line string, color gocui.Attribute) error {
	m.results = append(m.results, line)
	m.resultCs = append(m.resultCs, color)
	return nil
}
func (m *mockGUIForScraper) ClearResults()                                      {}
func (m *mockGUIForScraper) GetGui() *gocui.Gui                                 { return nil }

func TestScrapingState_ThreadSafety(t *testing.T) {
	s := &ScrapingState{}

	s.SetRunning(true)
	if !s.IsRunning() {
		t.Error("expected running=true")
	}

	s.IncrementSuccess()
	s.IncrementSuccess()
	s.IncrementFailed()
	s.UpdateProgress(5, 10)

	if s.Success != 2 {
		t.Errorf("success: expected 2, got %d", s.Success)
	}
	if s.Failed != 1 {
		t.Errorf("failed: expected 1, got %d", s.Failed)
	}
	if s.Current != 5 {
		t.Errorf("current: expected 5, got %d", s.Current)
	}
	if s.Total != 10 {
		t.Errorf("total: expected 10, got %d", s.Total)
	}

	s.SetRunning(false)
	if s.IsRunning() {
		t.Error("expected running=false")
	}
}

func TestScraperHandleEvent(t *testing.T) {
	mock := &mockGUIForScraper{}
	scraper := &Scraper{gui: mock, state: &ScrapingState{}}

	tests := []struct {
		name   string
		input  commands.Event
		verify func(*ScrapingState) bool
	}{
		{
			name:  "progress event",
			input: commands.Event{Type: "progress", Current: 3, Total: 10},
			verify: func(s *ScrapingState) bool {
				return s.Current == 3 && s.Total == 10
			},
		},
		{
			name:  "success event",
			input: commands.Event{Type: "success", File: "ssis-123.mp4"},
			verify: func(s *ScrapingState) bool {
				return s.Success == 1
			},
		},
		{
			name:  "failure event",
			input: commands.Event{Type: "failure", File: "unknown.mp4", Reason: "timeout"},
			verify: func(s *ScrapingState) bool {
				return s.Failed == 1
			},
		},
		{
			name:  "done event",
			input: commands.Event{Type: "done", Total: 10, Success: 8, Failed: 2},
			verify: func(s *ScrapingState) bool {
				return s.Total == 10 && s.Success == 8 && s.Failed == 2
			},
		},
		{
			name:  "unknown type ignored",
			input: commands.Event{Type: "bogus"},
			verify: func(s *ScrapingState) bool { return true },
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			scraper.handleEvent(tt.input)
			if !tt.verify(scraper.state) {
				t.Errorf("state verification failed after: %s", tt.input.Type)
			}
		})
	}
}

func TestScraperHandleEvent_Sequence(t *testing.T) {
	mock := &mockGUIForScraper{}
	scraper := &Scraper{gui: mock, state: &ScrapingState{}}

	// Simulate a full scrape session
	scraper.handleEvent(commands.Event{Type: "progress", Current: 1, Total: 3, File: "a.mp4"})
	scraper.handleEvent(commands.Event{Type: "log", Msg: "Starting scrape"})
	scraper.handleEvent(commands.Event{Type: "success", File: "a.mp4", Suffix: "-C"})
	scraper.handleEvent(commands.Event{Type: "progress", Current: 2, Total: 3, File: "b.mp4"})
	scraper.handleEvent(commands.Event{Type: "failure", File: "b.mp4", Reason: "timeout"})
	scraper.handleEvent(commands.Event{Type: "progress", Current: 3, Total: 3, File: "c.mp4"})
	scraper.handleEvent(commands.Event{Type: "success", File: "c.mp4"})
	scraper.handleEvent(commands.Event{Type: "done", Total: 3, Success: 2, Failed: 1})

	s := scraper.state
	if s.Success != 2 {
		t.Errorf("success: expected 2, got %d", s.Success)
	}
	if s.Failed != 1 {
		t.Errorf("failed: expected 1, got %d", s.Failed)
	}
	if len(mock.results) != 3 {
		t.Errorf("results count: expected 3, got %d", len(mock.results))
	}
}

func TestScraperHandleLogEvents(t *testing.T) {
	mock := &mockGUIForScraper{}
	scraper := &Scraper{gui: mock, state: &ScrapingState{}}

	scraper.handleEvent(commands.Event{Type: "log", Msg: "[INFO] Starting"})
	scraper.handleEvent(commands.Event{Type: "log", Msg: "[ERROR] Failed"})

	if len(mock.logs) != 2 {
		t.Errorf("log count: expected 2, got %d", len(mock.logs))
	}
	if mock.logs[0] != "[INFO] Starting" {
		t.Errorf("log[0]: expected '[INFO] Starting', got %q", mock.logs[0])
	}
}
