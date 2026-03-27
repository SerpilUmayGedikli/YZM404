from dataclasses import dataclass
from enum import Enum

class Topology(Enum):
    CENTRALIZED="centralized"
    DECENTRALIZED_FLAT="decentralized_flat"
    HIERARCHICAL="hierarchical"
    DYNAMIC="dynamic"

class CommunicationProtocol(Enum):
    NATURAL_LANGUAGE="natural_language"
    STRUCTURED_ARTIFACTS="structured_artifacts"
    SHARED_MEMORY="shared_memory"
    EVENT_BUS="event_bus"

class ConflictResolution(Enum):
    ARBITRATOR="arbitrator"
    VOTING="voting"
    DEBATE="debate"
    CONSENSUS="consensus"
    METACOGNITIVE="metacognitive"

class TaskDecomposition(Enum):
    NONE="none"
    PREDEFINED="predefined"
    LLM_PLANNED="llm_planned"
    ADAPTIVE="adaptive"

@dataclass
class Strategy:
    name: str
    topology: Topology
    communication: CommunicationProtocol
    resolution: ConflictResolution
    decomposition: TaskDecomposition

STRATEGIES = {
    "S1": Strategy("Solo", Topology.CENTRALIZED, CommunicationProtocol.NATURAL_LANGUAGE, ConflictResolution.ARBITRATOR, TaskDecomposition.NONE),
    "S1+": Strategy("Solo+SelfRefine", Topology.CENTRALIZED, CommunicationProtocol.NATURAL_LANGUAGE, ConflictResolution.METACOGNITIVE, TaskDecomposition.LLM_PLANNED),
    "S3": Strategy("SequentialChain", Topology.CENTRALIZED, CommunicationProtocol.STRUCTURED_ARTIFACTS, ConflictResolution.CONSENSUS, TaskDecomposition.PREDEFINED),
    "S4": Strategy("Hierarchical", Topology.HIERARCHICAL, CommunicationProtocol.STRUCTURED_ARTIFACTS, ConflictResolution.ARBITRATOR, TaskDecomposition.PREDEFINED),
    "S5": Strategy("Debate", Topology.DECENTRALIZED_FLAT, CommunicationProtocol.NATURAL_LANGUAGE, ConflictResolution.DEBATE, TaskDecomposition.LLM_PLANNED),
    "S6": Strategy("MajorityVoting", Topology.DECENTRALIZED_FLAT, CommunicationProtocol.NATURAL_LANGUAGE, ConflictResolution.VOTING, TaskDecomposition.NONE),
    "S7": Strategy("DynamicTeam", Topology.DYNAMIC, CommunicationProtocol.EVENT_BUS, ConflictResolution.CONSENSUS, TaskDecomposition.ADAPTIVE),
    "S8": Strategy("SharedMemoryCrew", Topology.CENTRALIZED, CommunicationProtocol.SHARED_MEMORY, ConflictResolution.CONSENSUS, TaskDecomposition.PREDEFINED),
    "S9": Strategy("SupervisorWorkers", Topology.HIERARCHICAL, CommunicationProtocol.EVENT_BUS, ConflictResolution.ARBITRATOR, TaskDecomposition.ADAPTIVE),
}

FRAMEWORK_MAP = {
    "autogen": STRATEGIES["S4"],
    "crewai": STRATEGIES["S4"],
    "metagpt": STRATEGIES["S4"],
    "langgraph": STRATEGIES["S7"],
    "openai_swarm": STRATEGIES["S8"],
}

def classify(framework_name: str) -> Strategy:
    return FRAMEWORK_MAP[framework_name.strip().lower()]
