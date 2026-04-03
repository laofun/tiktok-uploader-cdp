# Step Detail - Interactivity, Visibility, Description

## A) Interactivity toggles

### Inputs

- `comment` (bool)
- `duet` (bool)
- `stitch` (bool)

### Selector keys

- `comment_toggle`
- `duet_toggle`
- `stitch_toggle`

### Logic

1. Find toggle locator via candidate chain.
2. Try to read `is_checked()`.
3. If current != desired, click once.
4. Ignore exceptions per-toggle to keep run moving.

### Observability

- Step name: `set_interactivity`
- Detail payload: `comment=<v>,duet=<v>,stitch=<v>`

## B) Visibility

### Input

- `visibility`: `everyone | friends | only_you`

### Behavior

- `everyone`: no-op return.
- `friends` or `only_you`:
1. open dropdown
2. map value to text (`Friends`, `Only you`)
3. build option XPath from template
4. scroll and click option

### Selector keys

- `visibility_dropdown`
- `visibility_option_xpath_template`

## C) Description + hashtag/mention dropdown interaction

### Input

- `description` string

### Base process

1. Focus description editable node.
2. Select-all + backspace to clear.
3. Split text by spaces and process token-by-token.

### Token classes

#### Plain token

- Type `token + space`.

#### Hashtag token (`#tag`)

1. Type hashtag token.
2. Sleep 0.3s.
3. Try detect hashtag suggestion list (`mention_box`).
4. If suggestion popup visible, press Enter.
5. Type trailing space.

#### Mention token (`@user`)

1. Type mention token.
2. Sleep 0.5s.
3. Read candidate rows (`mention_user_id`).
4. Compare first word against target username (case-insensitive).
5. ArrowDown to matching row index.
6. Enter to select.
7. If no match/exception: fallback to inserting space.

### Reliability caveats

- Strongly dependent on language/localization and dropdown DOM.
- Mention list can be lazy-rendered; timing tune may be needed in config.
