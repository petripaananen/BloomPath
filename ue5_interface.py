import os
import logging
import time
import json
from typing import Optional, Any
from functools import wraps
from middleware.special_agent import CLIENT as AGENT

logger = logging.getLogger("BloomPath.UE5Interface")

# Configuration
# We keep the Actor Path as a fallback, but we will primarily search by Tag
UE5_ACTOR_PATH = os.getenv("UE5_ACTOR_PATH", "/Game/Garden.Garden:PersistentLevel.BP_GrowerActor_C_UAID_E89C257B5B95AEB802_2047448423")
UE5_ACTOR_TAG = "GrowerActor" # Ensure the BP has this tag, or we find by class

PRIORITY_COLORS = {
    "Highest": {"R": 1.0, "G": 0.2, "B": 0.2},
    "High": {"R": 1.0, "G": 0.6, "B": 0.1},
    "Medium": {"R": 0.3, "G": 0.8, "B": 0.3},
    "Low": {"R": 0.4, "G": 0.6, "B": 0.4},
    "Lowest": {"R": 0.5, "G": 0.5, "B": 0.5},
}

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry a function on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception: Optional[Exception] = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            logger.error(f"All {max_retries} attempts failed")
            raise last_exception
        return wrapper
    return decorator

@retry_on_failure()
def trigger_ue5_growth(
    branch_id: str,
    growth_type: str = "leaf",
    growth_modifier: float = 1.0,
    color: Optional[dict[str, float]] = None,
    epic_key: Optional[str] = None
) -> dict[str, Any]:
    if color is None:
        color = PRIORITY_COLORS.get("Medium")
        
    c_r = color.get('R', 0.3)
    c_g = color.get('G', 0.8)
    c_b = color.get('B', 0.3)

    logger.info(f"Triggering UE5 growth: {branch_id}")
    
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")

if actor:
    # Run script with kwargs (Validated names: target_branch_id, growth_type, growth_factor, color_r...)
    # Note: We construct the dictionary string manually for the embedded script
    # c_r, c_g, c_b are Python variables here, we insert their VALUES into the script string
    # Verified Positional Signature (6 args): 
    # (branch_id: str, r: float, g: float, b: float, epic_id: str, growth_modifier: float)
    # Note: growth_type is implicit in the function name "Grow_Leaves"
    actor.call_method("Grow_Leaves", (
        "{branch_id}", 
        {c_r}, 
        {c_g}, 
        {c_b}, 
        "{epic_key or ''}", 
        {growth_modifier}
    ))
    print("Success")
else:
    print("Error: Actor not found")
"""
    output = AGENT.execute_python(script)
    return {"output": output}

@retry_on_failure()
def trigger_ue5_shrink(branch_id: str) -> dict[str, Any]:
    logger.info(f"Triggering UE5 shrink: {branch_id}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    actor.call_method("Shrink_Leaves", ("{branch_id}",))
    print("Success")
"""
    return {"output": AGENT.execute_python(script)}

@retry_on_failure()
def trigger_ue5_thorns(branch_id: str, epic_key: Optional[str] = None) -> dict[str, Any]:
    logger.info(f"Triggering UE5 thorns: {branch_id}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    actor.call_method("Add_Thorns", ("{branch_id}", "{epic_key or ''}"))
    print("Success")
"""
    return {"output": AGENT.execute_python(script)}

@retry_on_failure()
def trigger_ue5_remove_thorns(branch_id: str) -> dict[str, Any]:
    logger.info(f"Triggering UE5 remove thorns: {branch_id}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    actor.call_method("Remove_Thorns", ("{branch_id}",))
    print("Success")
"""
    return {"output": AGENT.execute_python(script)}

@retry_on_failure()
def trigger_ue5_weather(weather: str) -> dict[str, Any]:
    logger.info(f"Setting UE5 weather: {weather}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    actor.Set_Weather("{weather}")
"""
    return {"output": AGENT.execute_python(script)}

@retry_on_failure()
def trigger_ue5_time(progress: float) -> dict[str, Any]:
    logger.info(f"Setting UE5 time: {progress:.2%}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    actor.Set_Time_Of_Day({progress})
"""
    return {"output": AGENT.execute_python(script)}

@retry_on_failure()
def trigger_ue5_set_tag(actor_name: str, tag: str) -> dict[str, Any]:
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    actor.Set_Actor_Tag("{actor_name}", "{tag}")
"""
    return {"output": AGENT.execute_python(script)}

@retry_on_failure()
def trigger_ue5_spawn_avatar(
    account_id: str,
    display_name: str,
    position: dict[str, float],
    avatar_url: str = ""
) -> dict[str, Any]:
    logger.info(f"👤 Spawning avatar for {display_name}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    # Spawn_Avatar(Avatar_ID, Display_Name, PosX, PosY, PosZ, URL)
    actor.Spawn_Avatar("{account_id}", "{display_name}", 
        {position.get('x', 0.0)}, {position.get('y', 0.0)}, {position.get('z', 0.0)}, 
        "{avatar_url}")
"""
    return {"output": AGENT.execute_python(script)}

@retry_on_failure()
def trigger_ue5_play_sound_2d(
    sound_name: str,
    volume_multiplier: float = 1.0,
    pitch_multiplier: float = 1.0
) -> dict[str, Any]:
    logger.info(f"🔊 Playing sound: {sound_name}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    # Play_Sound_2D(Name, Volume, Pitch)
    actor.Play_Sound_2D("{sound_name}", {volume_multiplier}, {pitch_multiplier})
"""
    return {"output": AGENT.execute_python(script)}

@retry_on_failure()
def trigger_phantom_warning(
    location_name: str,
    risk_level: float = 0.5
) -> dict[str, Any]:
    logger.info(f"👻 Spawning phantom at {location_name}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    actor.Spawn_Phantom_Hazard("{location_name}", {max(0.1, min(1.0, risk_level))})
"""
    return {"output": AGENT.execute_python(script)}

@retry_on_failure()
def trigger_ue5_load_level(file_path: str) -> dict[str, Any]:
    logger.info(f"🏗️ Loading generated level: {file_path}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    actor.Load_Generated_Level(r"{file_path}")
"""
    return {"output": AGENT.execute_python(script)}

# Map semantic type to actor (Helper, pure logic)
def map_semantic_type_to_actor(semantic_type: str) -> Optional[str]:
    st = semantic_type.lower()
    if "path" in st or "ground" in st:
        return "Floor"
    elif "wall" in st:
        return "Wall_North"
    elif "water" in st:
        return "Pond_Surface"
    return None

VINE_STYLES = {
    "blocked_by": {"color": {"R": 0.8, "G": 0.1, "B": 0.1}, "thickness": 0.15, "has_thorns": True, "animation": "pulse_warning"},
    "blocks": {"color": {"R": 0.8, "G": 0.4, "B": 0.1}, "thickness": 0.12, "has_thorns": True, "animation": "pulse_slow"},
    "relates_to": {"color": {"R": 0.3, "G": 0.7, "B": 0.3}, "thickness": 0.08, "has_thorns": False, "animation": "none"},
    "parent": {"color": {"R": 0.4, "G": 0.3, "B": 0.2}, "thickness": 0.2, "has_thorns": False, "animation": "none"},
    "child": {"color": {"R": 0.5, "G": 0.8, "B": 0.5}, "thickness": 0.06, "has_thorns": False, "animation": "none"}
}

@retry_on_failure()
def trigger_ue5_dependency_vine(from_id: str, to_id: str, relation_type: str = "relates_to") -> dict:
    style = VINE_STYLES.get(relation_type, VINE_STYLES["relates_to"])
    c = style["color"]
    vine_id = f"vine_{from_id}_{to_id}_{relation_type}"
    
    logger.info(f"🔗 Spawning vine {from_id}->{to_id}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    # Spawn_Dependency_Vine(Vine_ID, From, To, Type, Color_R, G, B, Thick, Thorns, Anim)
    actor.Spawn_Dependency_Vine("{vine_id}", "{from_id}", "{to_id}", "{relation_type}", 
        {c['R']}, {c['G']}, {c['B']}, {style['thickness']}, {style['has_thorns']}, "{style['animation']}")
"""
    return {"output": AGENT.execute_python(script)}

@retry_on_failure()
def trigger_ue5_remove_vine(from_id: str, to_id: str, relation_type: str = "relates_to") -> dict:
    vine_id = f"vine_{from_id}_{to_id}_{relation_type}"
    logger.info(f"✂️ Removing vine {vine_id}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    actor.Remove_Dependency_Vine("{vine_id}")
"""
    return {"output": AGENT.execute_python(script)}

@retry_on_failure()
def trigger_ue5_sync_all_vines(dependencies: list[dict]) -> dict:
    logger.info(f"🔄 Syncing vines batch")
    deps_json = json.dumps(dependencies).replace('"', '\\"') # Escape quotes for the python script string
    
    script = f"""
import unreal
import json
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    deps_raw = "{deps_json}"
    deps = json.loads(deps_raw)
    count = 0
    for d in deps:
        rel_type = d.get('relation_type', 'relates_to')
        style = {{
            'blocked_by': {{'r':0.8,'g':0.1,'b':0.1, 'th':0.15, 'thorn':True, 'anim':'pulse_warning'}},
            'blocks': {{'r':0.8,'g':0.4,'b':0.1, 'th':0.12, 'thorn':True, 'anim':'pulse_slow'}},
            'relates_to': {{'r':0.3,'g':0.7,'b':0.3, 'th':0.08, 'thorn':False, 'anim':'none'}},
            'parent': {{'r':0.4,'g':0.3,'b':0.2, 'th':0.2, 'thorn':False, 'anim':'none'}},
            'child': {{'r':0.5,'g':0.8,'b':0.5, 'th':0.06, 'thorn':False, 'anim':'none'}}
        }}.get(rel_type, {{'r':0.3,'g':0.7,'b':0.3, 'th':0.08, 'thorn':False, 'anim':'none'}})
        
        vine_id = f"vine_{{d['from_id']}}_{{d['to_id']}}_{{rel_type}}"
        
        actor.Spawn_Dependency_Vine(vine_id, d['from_id'], d['to_id'], rel_type, 
            style['r'], style['g'], style['b'], style['th'], style['thorn'], style['anim'])
        count += 1
    print(f"Synced {{count}} vines")
"""
    return {"output": AGENT.execute_python(script)}


@retry_on_failure()
def trigger_ue5_move_avatar(user_id: str, target_issue_id: str) -> dict[str, Any]:
    logger.info(f"👤 Moving avatar {user_id} to {target_issue_id}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    actor.Move_Avatar("{user_id}", "{target_issue_id}")
    print("Success")
"""
    return {"output": AGENT.execute_python(script)}


@retry_on_failure()
def trigger_ue5_remove_avatar(user_id: str) -> dict[str, Any]:
    logger.info(f"👤 Removing avatar {user_id}")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    actor.Remove_Avatar("{user_id}")
    print("Success")
"""
    return {"output": AGENT.execute_python(script)}


@retry_on_failure()
def trigger_ue5_ambience(intensity: float) -> dict[str, Any]:
    logger.info(f"🔊 Setting ambience intensity: {intensity:.2f}")
    # Clamp between 0.0 and 1.0
    val = max(0.0, min(1.0, intensity))
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    actor.Set_Ambience_Intensity({val})
"""
    return {"output": AGENT.execute_python(script)}


@retry_on_failure()
def trigger_ue5_reset_garden() -> dict[str, Any]:
    logger.info("Executed: Reset_Garden (Clear All)")
    script = f"""
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "{UE5_ACTOR_TAG}")
actor = actors[0] if actors else unreal.find_object(None, "{UE5_ACTOR_PATH}")
if actor:
    # Assuming Blueprint has a 'Reset_Garden' function that clears arrays/actors
    actor.call_method("Reset_Garden", ())
    print("Success")
"""
    return {"output": AGENT.execute_python(script)}
