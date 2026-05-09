from dataclasses import dataclass
@dataclass
class Chunk:
    text:str
    file_path:str
    language:str    
    start_line:int
    end_line:int
    chunk_type:str
    name:str
    repo_name:str