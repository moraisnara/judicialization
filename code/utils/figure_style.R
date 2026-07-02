# Shared figure style for the electoral-judicialization deck.
# ---------------------------------------------------------------------------
# ONE source of truth for figure colors and theme, so every figure matches the
# Beamer deck (colors below are the RGB values defined in slides_report.tex).
#
# Standing convention (see CLAUDE.md "Figure conventions"):
#   * Figure TITLES and FOOTNOTES live on the Beamer frame, NOT baked into the
#     image. `theme_report()` therefore BLANKS plot.title/subtitle/caption — do
#     not fight it; put that text in the frame title and a \caption/footnotesize
#     line on the slide.
#   * Use PAL / PAL_CYCLE for color, never ad-hoc hex.
#
# Usage:  source(file.path(UTILS, "figure_style.R"))  # UTILS = code/utils
#         ggplot(...) + ... + scale_color_manual(values = PAL_CYCLE) + theme_report()

suppressPackageStartupMessages(library(ggplot2))

# -- palette (matches the Beamer preamble \definecolor RGB values) ----------
PAL <- c(
  blue  = "#005A9C",  # myblue   RGB(0,90,156)
  red   = "#B41E1E",  # myred    RGB(180,30,30)
  green = "#00783C",  # mygreen  RGB(0,120,60)
  gray  = "#828282",  # mygray   RGB(130,130,130)
  light = "#DCE6F2"   # mylight  RGB(220,230,242)
)

# Electoral-cycle series colors (used by every 2020-vs-2024 time series).
PAL_CYCLE <- c("2020" = unname(PAL["gray"]), "2024" = unname(PAL["blue"]))

# Signed-effect colors (positive / negative), matching the deck's \pos / \negt.
PAL_SIGN <- c(pos = unname(PAL["green"]), neg = unname(PAL["red"]))

# -- theme ------------------------------------------------------------------
# theme_report() enforces the "no title/footnote in the image" rule by blanking
# them; axis titles are kept (they are structural, not editorial).
theme_report <- function(base_size = 11, ...) {
  theme_minimal(base_size = base_size) +
    theme(
      panel.grid.minor   = element_blank(),
      panel.grid.major.y = element_line(color = "grey90"),
      panel.grid.major.x = element_blank(),
      axis.line.x        = element_line(color = "grey40"),
      plot.title    = element_blank(),  # -> Beamer frame title
      plot.subtitle = element_blank(),  # -> Beamer frame
      plot.caption  = element_blank(),  # -> Beamer footnote
      legend.title  = element_blank(),
      legend.background = element_rect(fill = "white", color = NA),
      ...
    )
}
