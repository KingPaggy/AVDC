package controllers

import (
	"os"
	"path/filepath"
	"testing"
)

func TestReadIniFile(t *testing.T) {
	t.Run("standard format", func(t *testing.T) {
		tmp := t.TempDir()
		path := filepath.Join(tmp, "test.ini")
		os.WriteFile(path, []byte("[common]\nmain_mode = 1\nsoft_link = 0\n"), 0644)

		data, err := readIniFile(path)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if data["common"]["main_mode"] != "1" {
			t.Errorf("expected main_mode=1, got %q", data["common"]["main_mode"])
		}
		if data["common"]["soft_link"] != "0" {
			t.Errorf("expected soft_link=0, got %q", data["common"]["soft_link"])
		}
	})

	t.Run("multiple sections", func(t *testing.T) {
		tmp := t.TempDir()
		path := filepath.Join(tmp, "test.ini")
		content := `[common]
main_mode = 1
[proxy]
proxy = http://127.0.0.1:7890
timeout = 10
[emby]
emby_url = http://localhost:8096
`
		os.WriteFile(path, []byte(content), 0644)

		data, err := readIniFile(path)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if data["common"]["main_mode"] != "1" {
			t.Errorf("common/main_mode: expected 1, got %q", data["common"]["main_mode"])
		}
		if data["proxy"]["proxy"] != "http://127.0.0.1:7890" {
			t.Errorf("proxy/proxy: unexpected value %q", data["proxy"]["proxy"])
		}
		if data["emby"]["emby_url"] != "http://localhost:8096" {
			t.Errorf("emby/emby_url: unexpected value %q", data["emby"]["emby_url"])
		}
	})

	t.Run("skip comments and blank lines", func(t *testing.T) {
		tmp := t.TempDir()
		path := filepath.Join(tmp, "test.ini")
		content := `# comment
; another comment

[common]
# inline comment
mode = 2

`
		os.WriteFile(path, []byte(content), 0644)

		data, err := readIniFile(path)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if data["common"]["mode"] != "2" {
			t.Errorf("expected mode=2, got %q", data["common"]["mode"])
		}
	})

	t.Run("value containing equals sign", func(t *testing.T) {
		tmp := t.TempDir()
		path := filepath.Join(tmp, "test.ini")
		os.WriteFile(path, []byte("[emby]\napi_key = abc=def=ghi\n"), 0644)

		data, err := readIniFile(path)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if data["emby"]["api_key"] != "abc=def=ghi" {
			t.Errorf("expected 'abc=def=ghi', got %q", data["emby"]["api_key"])
		}
	})

	t.Run("file not found", func(t *testing.T) {
		_, err := readIniFile("/nonexistent/path/file.ini")
		if err == nil {
			t.Error("expected error for nonexistent file")
		}
	})
}

func TestWriteIniFile(t *testing.T) {
	t.Run("roundtrip", func(t *testing.T) {
		tmp := t.TempDir()
		path := filepath.Join(tmp, "test.ini")

		data := map[string]map[string]string{
			"common": {
				"main_mode": "1",
				"soft_link": "0",
			},
			"proxy": {
				"proxy":   "http://127.0.0.1:7890",
				"timeout": "10",
			},
		}

		if err := writeIniFile(path, data); err != nil {
			t.Fatalf("write failed: %v", err)
		}

		read, err := readIniFile(path)
		if err != nil {
			t.Fatalf("read failed: %v", err)
		}
		if read["common"]["main_mode"] != "1" {
			t.Errorf("main_mode: expected 1, got %q", read["common"]["main_mode"])
		}
		if read["proxy"]["proxy"] != "http://127.0.0.1:7890" {
			t.Errorf("proxy: unexpected value %q", read["proxy"]["proxy"])
		}
	})

	t.Run("value overwrite", func(t *testing.T) {
		tmp := t.TempDir()
		path := filepath.Join(tmp, "test.ini")

		// Write initial
		data := map[string]map[string]string{
			"common": {"main_mode": "1"},
		}
		if err := writeIniFile(path, data); err != nil {
			t.Fatalf("write failed: %v", err)
		}

		// Read, modify, write
		read, _ := readIniFile(path)
		read["common"]["main_mode"] = "2"
		read["proxy"] = map[string]string{"timeout": "30"}
		if err := writeIniFile(path, read); err != nil {
			t.Fatalf("write failed: %v", err)
		}

		// Verify
		final, _ := readIniFile(path)
		if final["common"]["main_mode"] != "2" {
			t.Errorf("expected main_mode=2, got %q", final["common"]["main_mode"])
		}
		if final["proxy"]["timeout"] != "30" {
			t.Errorf("expected timeout=30, got %q", final["proxy"]["timeout"])
		}
	})

	t.Run("empty section not written", func(t *testing.T) {
		tmp := t.TempDir()
		path := filepath.Join(tmp, "test.ini")

		data := map[string]map[string]string{
			"common": {"mode": "1"},
			"empty":  {},
		}

		if err := writeIniFile(path, data); err != nil {
			t.Fatalf("write failed: %v", err)
		}

		content, _ := os.ReadFile(path)
		cs := string(content)
		if len(cs) > 7 && cs[:7] == "[empty]" {
			t.Error("empty section should not be written")
		}
	})
}
