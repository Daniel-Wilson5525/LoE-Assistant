from dataclasses import dataclass
from typing import Callable

# ⬇️ import submodules directly
from services.generator.modes.rack_stack import prompt as rs_prompt, post as rs_post
from services.generator.modes.default    import prompt as df_prompt, post as df_post

@dataclass
class Mode:
    key: str
    prompt_dir: str
    build_prompt: Callable[[dict], str]
    post_process: Callable[[dict, dict], dict]

MODES = {
    "rack_stack": Mode(
        "rack_stack",
        "services/generator/modes/rack_stack",
        rs_prompt.build_prompt,
        rs_post.post_process,
    ),
    "default": Mode(
        "default",
        "services/generator/modes/default",
        df_prompt.build_prompt,
        df_post.post_process,
    ),
}

def get_mode(loe_type: str | None) -> Mode:
    return MODES.get((loe_type or "").lower(), MODES["default"])
