package python

import (
	"encoding/json"
	"testing"
)

func TestScanResultJSONParsing(t *testing.T) {
	input := `{
		"files": [
			{"file": "/movies/SSIS-123.mp4", "name": "SSIS-123", "number": "SSIS-123", "dir": "/movies"},
			{"file": "/movies/ABP-456.mkv", "name": "ABP-456", "number": "ABP-456", "dir": "/movies"},
			{"file": "/movies/no_number.avi", "name": "no_number", "number": "", "dir": "/movies"}
		],
		"total": 3
	}`

	var result ScanResult
	if err := json.Unmarshal([]byte(input), &result); err != nil {
		t.Fatalf("failed to parse JSON: %v", err)
	}

	if result.Total != 3 {
		t.Errorf("expected total=3, got %d", result.Total)
	}
	if len(result.Files) != 3 {
		t.Fatalf("expected 3 files, got %d", len(result.Files))
	}

	if result.Files[0].Number != "SSIS-123" {
		t.Errorf("expected first file number=SSIS-123, got %s", result.Files[0].Number)
	}
	if result.Files[2].Number != "" {
		t.Errorf("expected third file number empty, got %s", result.Files[2].Number)
	}
	if result.Files[1].Dir != "/movies" {
		t.Errorf("expected second file dir=/movies, got %s", result.Files[1].Dir)
	}
}

func TestScanResultEmpty(t *testing.T) {
	input := `{"files": [], "total": 0}`

	var result ScanResult
	if err := json.Unmarshal([]byte(input), &result); err != nil {
		t.Fatalf("failed to parse JSON: %v", err)
	}

	if result.Total != 0 {
		t.Errorf("expected total=0, got %d", result.Total)
	}
	if len(result.Files) != 0 {
		t.Errorf("expected 0 files, got %d", len(result.Files))
	}
}

func TestScanFileFieldMapping(t *testing.T) {
	input := `{"file": "/a/b/c.mp4", "name": "c", "number": "ABC-123", "dir": "/a/b"}`

	var f ScanFile
	if err := json.Unmarshal([]byte(input), &f); err != nil {
		t.Fatalf("failed to parse JSON: %v", err)
	}

	if f.File != "/a/b/c.mp4" {
		t.Errorf("File = %s, want /a/b/c.mp4", f.File)
	}
	if f.Name != "c" {
		t.Errorf("Name = %s, want c", f.Name)
	}
	if f.Number != "ABC-123" {
		t.Errorf("Number = %s, want ABC-123", f.Number)
	}
	if f.Dir != "/a/b" {
		t.Errorf("Dir = %s, want /a/b", f.Dir)
	}
}
