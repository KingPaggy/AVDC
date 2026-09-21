package controllers

import (
	"os"
	"path/filepath"
	"strings"
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

// TestWriteIniFilePreserving 验证写回保留注释/空行/键顺序，
// 仅更新目标键，缺失键追加到 section 末尾，新 section 追加到
// 文件末尾。
func TestWriteIniFilePreserving(t *testing.T) {
	tmp := t.TempDir()
	path := filepath.Join(tmp, "config.ini")
	original := "# top comment\n[common]\nmain_mode = 1\n\n" +
		"# media note\nmedia_path = /old\n\n[proxy]\nproxy = \n"
	if err := os.WriteFile(path, []byte(original), 0644); err != nil {
		t.Fatal(err)
	}

	updates := map[string]map[string]string{
		"common": {"media_path": "/new", "extra_key": "x"},
		"emby":   {"api_key": "secret"},
	}
	if err := writeIniFilePreserving(path, updates); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	got := string(raw)

	for _, want := range []string{
		"# top comment", "# media note",
		"media_path = /new", "main_mode = 1",
		"extra_key = x", "[emby]", "api_key = secret",
	} {
		if !strings.Contains(got, want) {
			t.Errorf("expected output to contain %q, got:\n%s", want, got)
		}
	}
	if strings.Contains(got, "/old") {
		t.Errorf("old value should be replaced, got:\n%s", got)
	}
	if strings.Count(got, "[common]") != 1 {
		t.Errorf("section must not be duplicated, got:\n%s", got)
	}

	// 回读验证
	data, err := readIniFile(path)
	if err != nil {
		t.Fatalf("re-read: %v", err)
	}
	if data["common"]["media_path"] != "/new" {
		t.Errorf("media_path = %q, want /new",
			data["common"]["media_path"])
	}
	if data["common"]["extra_key"] != "x" {
		t.Errorf("extra_key = %q, want x", data["common"]["extra_key"])
	}
	if data["emby"]["api_key"] != "secret" {
		t.Errorf("api_key = %q, want secret", data["emby"]["api_key"])
	}
}
