from wagtail import hooks

FULL_RICH_TEXT_FEATURES = [
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "bold",
    "italic",
    "ol",
    "ul",
    "hr",
    "link",
    "document-link",
    "image",
    "embed",
    "code",
    "blockquote",
    "superscript",
    "subscript",
    "strikethrough",
]


@hooks.register("register_rich_text_features")
def register_full_rich_text_features(features):
    """Ensure a full feature set is available for RichTextField editors."""
    features.default_features = FULL_RICH_TEXT_FEATURES
