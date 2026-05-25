package util

import (
	"path/filepath"
	"regexp"
	"strings"
)

// Number extraction regex patterns — translated from Python core/_files/file_utils.py
var (
	reCD          = regexp.MustCompile(`(?i)-CD\d+`)
	reDate        = regexp.MustCompile(`-\d{4}-\d{1,2}-\d{1,2}|\d{4}-\d{1,2}-\d{1,2}-`)
	reEuropean    = regexp.MustCompile(`^\D+\.\d{2}\.\d{2}\.\d{2}`)
	reEuropeanNum = regexp.MustCompile(`\D+\.\d{2}\.\d{2}\.\d{2}`)
	reXXXAV       = regexp.MustCompile(`(?i)XXX-AV-\d{4,}`)
	reFC2         = regexp.MustCompile(`(?i)FC2-\d{5,}`)
	reNumAlphaDash   = regexp.MustCompile(`\d+[a-zA-Z]+-\d+`)
	reAlphaDashNum   = regexp.MustCompile(`[a-zA-Z]+-\d+`)
	reAlphaDashAlphaNum = regexp.MustCompile(`[a-zA-Z]+-[a-zA-Z]\d+`)
	reNumDashAlpha   = regexp.MustCompile(`\d+-[a-zA-Z]+`)
	reNumDash        = regexp.MustCompile(`\d+-\d+`)
	reNumUnder       = regexp.MustCompile(`\d+_\d+`)
	reAllNum         = regexp.MustCompile(`\d+`)
	reAllAlpha       = regexp.MustCompile(`\D+`)
	reEscapeSplit    = regexp.MustCompile(`[,，]`)
)

// ExtractNumber extracts a JAV movie number from a file path.
// Ported from Python core/_files/file_utils.py getNumber().
func ExtractNumber(filePath string, escapeString string) string {
	// Remove -C. suffix (e.g., SSIS-123-C.mp4 → SSIS-123.mp4)
	filePath = strings.ReplaceAll(filePath, "-C.", ".")
	filePath = strings.ReplaceAll(filePath, "-c.", ".")

	filename := strings.TrimSuffix(filepath.Base(filePath), filepath.Ext(filePath))

	// Remove escape strings
	for _, esc := range reEscapeSplit.Split(escapeString, -1) {
		esc = strings.TrimSpace(esc)
		if esc != "" && strings.Contains(filename, esc) {
			filename = strings.ReplaceAll(filename, esc, "")
		}
	}

	// Remove -CDn suffix
	if parts := reCD.FindAllString(filename, -1); len(parts) > 0 {
		for _, part := range parts {
			filename = strings.ReplaceAll(filename, part, "")
		}
	}

	// Remove date patterns
	filename = reDate.ReplaceAllString(filename, "")

	// European style: xxx.00.00.00
	if reEuropean.MatchString(filename) {
		if m := reEuropeanNum.FindString(filename); m != "" {
			return m
		}
		return strings.TrimSuffix(filepath.Base(filePath), filepath.Ext(filePath))
	}

	// XXX-AV style
	if m := reXXXAV.FindString(strings.ToUpper(filename)); m != "" {
		return m
	}

	// Contains - or _
	if strings.Contains(filename, "-") || strings.Contains(filename, "_") {
		upper := strings.ToUpper(filename)
		// FC2 style
		if strings.Contains(upper, "FC2") {
			filename = strings.ReplaceAll(upper, "PPV", "")
			filename = strings.ReplaceAll(filename, "--", "-")
		}
		if m := reFC2.FindString(filename); m != "" {
			return m
		}

		// Try patterns in priority order
		patterns := []*regexp.Regexp{
			reNumAlphaDash,
			reAlphaDashNum,
			reAlphaDashAlphaNum,
			reNumDashAlpha,
			reNumDash,
			reNumUnder,
		}
		for _, p := range patterns {
			if m := p.FindString(filename); m != "" {
				return m
			}
		}
		return filename
	}

	// No separator: try DMM style or fallback
	nums := reAllNum.FindAllString(filename, -1)
	alphas := reAllAlpha.FindAllString(filename, -1)
	if len(nums) > 0 && len(alphas) > 0 {
		if len(nums[0]) <= 4 && len(alphas[0]) > 1 {
			return alphas[0] + "-" + nums[0]
		}
	}
	return filename
}
