// Package python provides a client for calling the Python CLI (cli/cli.py).
// This eliminates duplicated logic between Go and Python for file scanning
// and number extraction.
package python

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

// Client wraps subprocess calls to cli.py.
type Client struct {
	projectRoot string
}

// ScanResult mirrors the JSON response from `cli.py scan`.
type ScanResult struct {
	Files []ScanFile `json:"files"`
	Total int        `json:"total"`
}

// ScanFile represents a single video file with extracted number.
type ScanFile struct {
	File   string `json:"file"`
	Name   string `json:"name"`
	Number string `json:"number"`
	Dir    string `json:"dir"`
}

// NewClient creates a new Python client.
// projectRoot is the directory containing cli/cli.py.
func NewClient(projectRoot string) *Client {
	return &Client{projectRoot: projectRoot}
}

// ProjectRoot returns the project root directory.
func (c *Client) ProjectRoot() string {
	return c.projectRoot
}

// Scan calls `cli.py scan --path dir` and returns the parsed result.
func (c *Client) Scan(dir string) (*ScanResult, error) {
	cliPath := filepath.Join(c.projectRoot, "cli", "cli.py")

	cmd := exec.Command("uv", "run", "python", cliPath, "scan", "--path", dir)
	cmd.Dir = c.projectRoot

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("python scan failed: %w\nstderr: %s", err, stderr.String())
	}

	var result ScanResult
	if err := json.Unmarshal(stdout.Bytes(), &result); err != nil {
		return nil, fmt.Errorf("failed to parse scan result: %w\noutput: %s", err, stdout.String())
	}

	return &result, nil
}

// FindProjectRoot searches upward for the directory containing cli/cli.py.
// It walks up to 10 parent directories from the current working directory.
func FindProjectRoot() string {
	dir, err := os.Getwd()
	if err != nil {
		return ""
	}
	for i := 0; i < 10; i++ {
		cliPath := filepath.Join(dir, "cli", "cli.py")
		if _, err := os.Stat(cliPath); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return ""
}
