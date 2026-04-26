import os

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(APP_DIR, "hsk3.xlsx")
PROGRESS_FILE = os.path.join(APP_DIR, "progress.json")
AVATAR_OPTIONS = ["😀", "😎", "🤓", "🧐", "🎯", "🌟", "📚", "🚀"]

# Key untuk session state yang perlu di-persist
PERSISTED_SET_KEYS = {
    "quiz_answered_set", "cloze_answered_set", "scramble_scored_set",
    "wrong_quiz", "wrong_cloze", "wrong_scramble", "favorites", "mastered_vocab",
}
PERSISTED_KEYS = [
    "profile_name", "profile_avatar", "theme_mode", "menu", "fc_page",
    "selected_hanzi", "score_quiz", "score_cloze", "score_scramble",
    "quiz_answered_set", "cloze_answered_set", "scramble_scored_set",
    "wrong_quiz", "wrong_cloze", "wrong_scramble", "rep_mode", "quiz_idx",
    "quiz_mode", "clz_idx", "sc_idx", "flashcard_search", "hide_mastered",
    "favorites", "mastered_vocab", "daily_target", "current_streak",
    "best_streak", "quiz_attempts", "quiz_correct_attempts", "cloze_attempts",
    "cloze_correct_attempts", "scramble_attempts", "scramble_correct_attempts",
]