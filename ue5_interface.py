
import os
import requests
import logging
import time
from typing import Optional, Any
from functools import wraps

logger = logging.getLogger("BloomPath.UE5Interface")

# Configuration
UE5_REMOTE_CONTROL_URL = os.getenv("UE5_REMOTE_CONTROL_URL", "http://localhost:8080/remote/object/call")
UE5_ACTOR_PATH = os.getenv("UE5_ACTOR_PATH", "/Game/Maps/Main.Main:PersistentLevel.GrowerActor")

# Function Names
UE5_GROW_FUNCTION = os.getenv("UE5_GROW_FUNCTION", "Grow_Leaves")
UE5_SHRINK_FUNCTION = os.getenv("UE5_SHRINK_FUNCTION", "Shrink_Leaves")
UE5_THORNS_FUNCTION = os.getenv("UE5_THORNS_FUNCTION", "Add_Thorns")
UE5_REMOVE_THORNS_FUNCTION = os.getenv("UE5_REMOVE_THORNS_FUNCTION", "Remove_Thorns")
UE5_WEATHER_FUNCTION = os.getenv("UE5_WEATHER_FUNCTION", "Set_Weather")
UE5_TIME_FUNCTION = os.getenv("UE5_TIME_FUNCTION", "Set_Time_Of_Day")
UE5_SET_TAG_FUNCTION = os.getenv("UE5_SET_TAG_FUNCTION", "Set_Actor_Tag")

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
    """Calls the UE5 Remote Control API to trigger the Grow_Leaves function."""
    if color is None:
        color = PRIORITY_COLORS.get("Medium")
    
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_GROW_FUNCTION,
        "parameters": {
            "Target_Branch_ID": branch_id,
            "Growth_Type": growth_type,
            "Growth_Modifier": growth_modifier,
            "Color_R": color.get("R", 0.3),
            "Color_G": color.get("G", 0.8),
            "Color_B": color.get("B", 0.3),
            "Epic_ID": epic_key or ""
        },
        "generateTransaction": True
    }
    
    logger.info(f"Triggering UE5 growth: {branch_id}")
    return _send_request(payload)

@retry_on_failure()
def trigger_ue5_shrink(branch_id: str) -> dict[str, Any]:
    """Calls the UE5 Remote Control API to trigger the Shrink_Leaves function."""
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_SHRINK_FUNCTION,
        "parameters": {
            "Target_Branch_ID": branch_id
        },
        "generateTransaction": True
    }
    
    logger.info(f"Triggering UE5 shrink: {branch_id}")
    return _send_request(payload)

@retry_on_failure()
def trigger_ue5_thorns(branch_id: str, epic_key: Optional[str] = None) -> dict[str, Any]:
    """Calls the UE5 Remote Control API to add thorns."""
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_THORNS_FUNCTION,
        "parameters": {
            "Target_Branch_ID": branch_id,
            "Epic_ID": epic_key or ""
        },
        "generateTransaction": True
    }
    logger.info(f"Triggering UE5 thorns: {branch_id}")
    return _send_request(payload)

@retry_on_failure()
def trigger_ue5_remove_thorns(branch_id: str) -> dict[str, Any]:
    """Calls the UE5 Remote Control API to remove thorns."""
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_REMOVE_THORNS_FUNCTION,
        "parameters": {
            "Target_Branch_ID": branch_id
        },
        "generateTransaction": True
    }
    logger.info(f"Triggering UE5 remove thorns: {branch_id}")
    return _send_request(payload)

@retry_on_failure()
def trigger_ue5_weather(weather: str) -> dict[str, Any]:
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_WEATHER_FUNCTION,
        "parameters": { "Weather_State": weather },
        "generateTransaction": True
    }
    logger.info(f"Setting UE5 weather: {weather}")
    return _send_request(payload)

@retry_on_failure()
def trigger_ue5_time(progress: float) -> dict[str, Any]:
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_TIME_FUNCTION,
        "parameters": { "Time_Progress": progress },
        "generateTransaction": True
    }
    logger.info(f"Setting UE5 time: {progress:.2%}")
    return _send_request(payload)

@retry_on_failure()
def trigger_ue5_set_tag(actor_name: str, tag: str) -> dict[str, Any]:
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_SET_TAG_FUNCTION,
        "parameters": {
            "Target_Actor_Name": actor_name,
            "Tag_To_Add": tag
        },
        "generateTransaction": True
    }
UE5_SPAWN_AVATAR_FUNCTION = os.getenv("UE5_SPAWN_AVATAR_FUNCTION", "Spawn_Avatar")

@retry_on_failure()
def trigger_ue5_spawn_avatar(
    account_id: str,
    display_name: str,
    position: dict[str, float],
    avatar_url: str = ""
) -> dict[str, Any]:
    """
    Calls the UE5 Remote Control API to spawn or update a team member avatar.
    
    Args:
        account_id: Unique Jira account ID.
        display_name: User's display name.
        position: Dict with 'x', 'y', 'z' coordinates.
        avatar_url: URL to the user's avatar image.
    """
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_SPAWN_AVATAR_FUNCTION,
        "parameters": {
            "Avatar_ID": account_id,
            "Display_Name": display_name,
            "Position_X": position.get('x', 0.0),
            "Position_Y": position.get('y', 0.0),
            "Position_Z": position.get('z', 0.0),
            "Avatar_URL": avatar_url
        },
        "generateTransaction": True
    }
    logger.info(f"👤 Spawning avatar for {display_name} at ({position.get('x')}, {position.get('y')})")
    return _send_request(payload)

UE5_PLAY_SOUND_FUNCTION = os.getenv("UE5_PLAY_SOUND_FUNCTION", "Play_Sound_2D")

@retry_on_failure()
def trigger_ue5_play_sound_2d(
    sound_name: str,
    volume_multiplier: float = 1.0,
    pitch_multiplier: float = 1.0
) -> dict[str, Any]:
    """
    Calls the UE5 Remote Control API to play a 2D sound.
    
    Args:
        sound_name: Name/ID of the sound to play (e.g., 'Success', 'Blocker', 'Grow').
        volume_multiplier: Volume scale.
        pitch_multiplier: Pitch scale.
    """
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_PLAY_SOUND_FUNCTION,
        "parameters": {
            "Sound_Name": sound_name,
            "Volume": volume_multiplier,
            "Pitch": pitch_multiplier
        },
        "generateTransaction": False # Sound doesn't need transaction tracking usually
    }
    logger.info(f"🔊 Playing sound: {sound_name}")
    return _send_request(payload)

UE5_PHANTOM_FUNCTION = os.getenv("UE5_PHANTOM_FUNCTION", "Spawn_Phantom_Hazard")

@retry_on_failure()
def trigger_phantom_warning(
    location_name: str,
    risk_level: float = 0.5
) -> dict[str, Any]:
    """
    Calls UE5 to spawn a 'Ghost Object' representing a predicted future failure (Latent Risk).
    
    Args:
        location_name: Name of the location/actor to spawn near (e.g. 'Location_Center').
        risk_level: 0.0 to 1.0 (Higher = Redder/More opaque).
    """
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_PHANTOM_FUNCTION,
        "parameters": {
            "Location_Name": location_name,
            "Risk_Opacity": max(0.1, min(1.0, risk_level)) # Clamp 0.1-1.0
        },
        "generateTransaction": True
    }
    logger.info(f"👻 Spawning Latent Risk Phantom at {location_name} (Risk: {risk_level:.2f})")
    return _send_request(payload)

def map_semantic_type_to_actor(semantic_type: str) -> Optional[str]:
    """
    Maps a semantic type (e.g., 'path', 'ground') to a UE5 Actor name.
    
    Args:
        semantic_type: String describing the object type.
        
    Returns:
        The name of the UE5 Actor (e.g., 'Floor') or None if no mapping exists.
    """
    st = semantic_type.lower()
    
    # Heuristic Mapping
    if "path" in st or "ground" in st:
        return "Floor"
    elif "wall" in st:
        return "Wall_North"  # Placeholder
    elif "water" in st:
        return "Pond_Surface"
    elif "stone" in st:
         # Future: return "Stone_Actor_BP"
         pass
         
    return None


# Vine Visualization Configuration
UE5_SPAWN_VINE_FUNCTION = os.getenv("UE5_SPAWN_VINE_FUNCTION", "Spawn_Dependency_Vine")
UE5_REMOVE_VINE_FUNCTION = os.getenv("UE5_REMOVE_VINE_FUNCTION", "Remove_Dependency_Vine")

# Vine appearance based on relation type
VINE_STYLES = {
    "blocked_by": {
        "color": {"R": 0.8, "G": 0.1, "B": 0.1},  # Red thorny vine
        "thickness": 0.15,
        "has_thorns": True,
        "animation": "pulse_warning"
    },
    "blocks": {
        "color": {"R": 0.8, "G": 0.4, "B": 0.1},  # Orange warning vine
        "thickness": 0.12,
        "has_thorns": True,
        "animation": "pulse_slow"
    },
    "relates_to": {
        "color": {"R": 0.3, "G": 0.7, "B": 0.3},  # Green connection vine
        "thickness": 0.08,
        "has_thorns": False,
        "animation": "none"
    },
    "parent": {
        "color": {"R": 0.4, "G": 0.3, "B": 0.2},  # Brown trunk-like
        "thickness": 0.2,
        "has_thorns": False,
        "animation": "none"
    },
    "child": {
        "color": {"R": 0.5, "G": 0.8, "B": 0.5},  # Light green
        "thickness": 0.06,
        "has_thorns": False,
        "animation": "none"
    }
}


@retry_on_failure()
def trigger_ue5_dependency_vine(
    from_id: str,
    to_id: str,
    relation_type: str = "relates_to"
) -> dict:
    """
    Spawn a vine mesh connecting two plants to visualize dependencies.
    
    Args:
        from_id: Source issue ID (e.g., "KAN-123")
        to_id: Target issue ID (e.g., "KAN-456")
        relation_type: Type of relation (blocked_by, blocks, relates_to, parent, child)
        
    Returns:
        Response from UE5
    """
    style = VINE_STYLES.get(relation_type, VINE_STYLES["relates_to"])
    
    # Create a unique identifier for this vine
    vine_id = f"vine_{from_id}_{to_id}_{relation_type}"
    
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_SPAWN_VINE_FUNCTION,
        "parameters": {
            "Vine_ID": vine_id,
            "From_Issue_Key": from_id,
            "To_Issue_Key": to_id,
            "Relation_Type": relation_type,
            "Vine_Color": style["color"],
            "Vine_Thickness": style["thickness"],
            "Has_Thorns": style["has_thorns"],
            "Animation_Style": style["animation"]
        },
        "generateTransaction": True
    }
    
    # Log with appropriate emoji based on relation type
    emoji = "🔗" if relation_type == "relates_to" else "🔴" if "block" in relation_type else "🌿"
    logger.info(f"{emoji} Spawning {relation_type} vine: {from_id} → {to_id}")
    
    return _send_request(payload)


@retry_on_failure()
def trigger_ue5_remove_vine(
    from_id: str,
    to_id: str,
    relation_type: str = "relates_to"
) -> dict:
    """
    Remove a dependency vine between two plants.
    
    Args:
        from_id: Source issue ID
        to_id: Target issue ID
        relation_type: Type of relation
        
    Returns:
        Response from UE5
    """
    vine_id = f"vine_{from_id}_{to_id}_{relation_type}"
    
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_REMOVE_VINE_FUNCTION,
        "parameters": {
            "Vine_ID": vine_id
        },
        "generateTransaction": True
    }
    
    logger.info(f"✂️ Removing vine: {from_id} → {to_id}")
    return _send_request(payload)


@retry_on_failure()
def trigger_ue5_sync_all_vines(dependencies: list[dict]) -> dict:
    """
    Sync all dependency vines at once (for initial state sync).
    
    Args:
        dependencies: List of dicts with from_id, to_id, relation_type
        
    Returns:
        Response from UE5
    """
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": "Sync_All_Vines",
        "parameters": {
            "Dependencies": dependencies
        },
        "generateTransaction": True
    }
    
    logger.info(f"🔄 Syncing {len(dependencies)} dependency vines")
    return _send_request(payload)


def _send_request(payload: dict) -> dict:
    response = requests.put(UE5_REMOTE_CONTROL_URL, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()

