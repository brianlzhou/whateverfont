# Softboil

## Brief

Make me a soft, rounded sans for a friendly app. Round every stroke end, but keep it calm enough for a
whole page of text.

- **What it is for:** a consumer app: chat bubbles, onboarding screens, buttons, a help page.
- **How it should feel:** friendly and soft, and still tidy.
- **What it must not look like:** a bubbly children's font, or letters that look inflated.
- **Styles:** Light, Regular, Medium, Semibold and Bold, an italic, and one variable font.

## Decisions

- Started from the `rounded` preset: `roundness` 1 ends every stroke in a half circle.
- Everything else is the proportion of an interface sans, so the round ends are the only soft thing: `xh`
  536, `counter` 268 with `round_width` 1.14, `cap_width` 1.12, `spacing` 1.2.
- `cut="flat"`: the curved strokes of `c e s a` end level, and the hooks of `f t j` and the arm of `r` stop
  as soon as they are level. With square cuts the round ends pointed in different directions and the text
  looked restless, and with longer hooks `t` and `j` ended in a curl.
- `superness` 0.2 squares the bowls slightly, which keeps them from looking like balloons.
- Weight 88 for the regular. Round ends make a stroke look shorter and lighter, so it is a little heavier
  than Dayshift.
- The bold is at weight 128, with `aperture` 0.65 and `arm` 1.2.

## Weak points

- The round ends hide most of what is rough in the bold, but its `s` is still narrow.
- The tilde of `ñ` is large.

## Feedback

Notes from the review board go here, with the date.
