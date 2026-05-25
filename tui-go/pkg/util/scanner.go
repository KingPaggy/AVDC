package util

import (
	"os"
	"path/filepath"
	"strings"
)

// VideoExtensions lists file extensions recognized as video files.
var VideoExtensions = map[string]bool{
	".mp4": true, ".avi": true, ".mkv": true, ".wmv": true,
	".flv": true, ".mov": true, ".m4v": true, ".webm": true,
	".rmvb": true, ".rm": true, ".3gp": true, ".ts": true,
}

// VideoFile represents a scanned video file with its extracted number.
type VideoFile struct {
	Path   string
	Name   string // filename without extension
	Number string // extracted movie number
	Dir    bool   // true if directory entry
}

// ScanDir scans a directory for video files and extracts movie numbers.
func ScanDir(dirPath string) ([]VideoFile, error) {
	entries, err := os.ReadDir(dirPath)
	if err != nil {
		return nil, err
	}

	var files []VideoFile
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		name := entry.Name()
		// Skip hidden files
		if strings.HasPrefix(name, ".") {
			continue
		}
		ext := strings.ToLower(filepath.Ext(name))
		if !VideoExtensions[ext] {
			continue
		}

		// Clean filepath
		fullPath := filepath.Join(dirPath, name)
		fullPath = filepath.ToSlash(fullPath)

		// Extract number
		number := ExtractNumber(fullPath, "")

		files = append(files, VideoFile{
			Path:   fullPath,
			Name:   strings.TrimSuffix(name, ext),
			Number: number,
		})
	}
	return files, nil
}
