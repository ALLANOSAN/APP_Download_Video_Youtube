import os
from pathlib import Path
from typing import Dict, Optional

class AgentManager:
    """Gerencia o carregamento de instruções de agentes da pasta .agent/agents."""
    
    def __init__(self, agents_dir: str = ".agent/agents"):
        # Busca o diretório raiz do projeto
        self.base_path = Path(__file__).parent.parent.parent / agents_dir
        self.agents: Dict[str, str] = {}
        self._load_agents()

    def _load_agents(self):
        """Carrega todos os arquivos .md ou .txt como instruções de agentes."""
        if not self.base_path.exists():
            return

        for file in self.base_path.glob("*"):
            if file.suffix in [".md", ".txt"]:
                agent_name = file.stem.lower()
                with open(file, "r", encoding="utf-8") as f:
                    self.agents[agent_name] = f.read()

    def get_agent_instructions(self, name: str) -> Optional[str]:
        """Retorna as instruções de um agente específico."""
        return self.agents.get(name.lower())

# Instância global para uso no app
agent_manager = AgentManager()
