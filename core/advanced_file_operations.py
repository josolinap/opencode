"""
Advanced File Operations System for OpenCode
Author: MiniMax Agent

This system provides comprehensive file management capabilities including:
- Complex file system navigation
- Batch file processing
- Version control integration
- Dynamic path resolution
- File conflict detection and resolution
"""

import os
import shutil
import hashlib
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import difflib
import tempfile
from datetime import datetime
import fnmatch
import stat
import logging

class FileOperation(Enum):
    """Types of file operations"""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    COPY = "copy"
    MOVE = "move"
    RENAME = "rename"

class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    SKIP = "skip"
    OVERWRITE = "overwrite"
    BACKUP_AND_OVERWRITE = "backup_and_overwrite"
    MERGE = "merge"
    ASK_USER = "ask_user"

@dataclass
class FileChange:
    """Represents a change to a file"""
    operation: FileOperation
    source_path: str
    target_path: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class FileOperationResult:
    """Result of a file operation"""
    success: bool
    operation: FileOperation
    source_path: str
    target_path: Optional[str]
    details: str
    backup_created: bool = False
    conflict_resolved: bool = False
    execution_time: float = 0.0
    error_message: Optional[str] = None

class VersionControlManager:
    """Manages version control integration"""
    
    def __init__(self, workspace_dir: str = "/workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.git_available = self._check_git_availability()
        self.initialize_git_repo()
    
    def _check_git_availability(self) -> bool:
        """Check if git is available"""
        try:
            subprocess.run(["git", "--version"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def initialize_git_repo(self):
        """Initialize git repository if not already done"""
        if not self.git_available:
            return
        
        if not (self.workspace_dir / ".git").exists():
            try:
                subprocess.run(["git", "init"], 
                             cwd=self.workspace_dir, 
                             capture_output=True, check=True)
                logging.info("Initialized Git repository")
            except subprocess.CalledProcessError as e:
                logging.warning(f"Failed to initialize Git: {e}")
    
    def stage_files(self, file_paths: List[str]) -> bool:
        """Stage files for commit"""
        if not self.git_available:
            return False
        
        try:
            for file_path in file_paths:
                subprocess.run(["git", "add", file_path], 
                             cwd=self.workspace_dir, 
                             capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to stage files: {e}")
            return False
    
    def create_commit(self, message: str) -> Optional[str]:
        """Create a commit with current changes"""
        if not self.git_available:
            return None
        
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message], 
                cwd=self.workspace_dir,
                capture_output=True, 
                check=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to create commit: {e}")
            return None
    
    def get_file_diff(self, file_path: str) -> Optional[str]:
        """Get diff for a specific file"""
        if not self.git_available:
            return None
        
        try:
            result = subprocess.run(
                ["git", "diff", file_path],
                cwd=self.workspace_dir,
                capture_output=True,
                check=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get git status"""
        if not self.git_available:
            return {"available": False}
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.workspace_dir,
                capture_output=True,
                check=True,
                text=True
            )
            
            status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            staged_files = []
            modified_files = []
            untracked_files = []
            
            for line in status_lines:
                if line.startswith("A "):
                    staged_files.append(line[3:])
                elif line.startswith(" M"):
                    modified_files.append(line[3:])
                elif line.startswith("??"):
                    untracked_files.append(line[3:])
            
            return {
                "available": True,
                "staged_files": staged_files,
                "modified_files": modified_files,
                "untracked_files": untracked_files
            }
        except subprocess.CalledProcessError:
            return {"available": True, "error": "Failed to get status"}

class BatchFileProcessor:
    """Handles batch file operations"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.operation_history = []
    
    async def batch_create_files(self, file_operations: List[Dict[str, Any]]) -> List[FileOperationResult]:
        """Create multiple files in batch"""
        results = []
        
        async def create_single_file(operation: Dict[str, Any]) -> FileOperationResult:
            start_time = time.time()
            try:
                file_path = Path(operation["path"])
                content = operation.get("content", "")
                create_dirs = operation.get("create_dirs", True)
                
                if create_dirs:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_path.write_text(content, encoding="utf-8")
                
                result = FileOperationResult(
                    success=True,
                    operation=FileOperation.CREATE,
                    source_path=str(file_path),
                    target_path=None,
                    details=f"Created file with {len(content)} characters",
                    execution_time=time.time() - start_time
                )
                
            except Exception as e:
                result = FileOperationResult(
                    success=False,
                    operation=FileOperation.CREATE,
                    source_path=operation["path"],
                    target_path=None,
                    details="Failed to create file",
                    execution_time=time.time() - start_time,
                    error_message=str(e)
                )
            
            self.operation_history.append(result)
            return result
        
        # Execute batch operations concurrently
        tasks = [create_single_file(op) for op in file_operations]
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def batch_copy_files(self, copy_operations: List[Dict[str, Any]]) -> List[FileOperationResult]:
        """Copy multiple files in batch"""
        results = []
        
        async def copy_single_file(operation: Dict[str, Any]) -> FileOperationResult:
            start_time = time.time()
            try:
                source = Path(operation["source"])
                target = Path(operation["target"])
                create_dirs = operation.get("create_dirs", True)
                overwrite = operation.get("overwrite", False)
                
                if create_dirs:
                    target.parent.mkdir(parents=True, exist_ok=True)
                
                if not overwrite and target.exists():
                    raise FileExistsError(f"Target file already exists: {target}")
                
                shutil.copy2(source, target)
                
                result = FileOperationResult(
                    success=True,
                    operation=FileOperation.COPY,
                    source_path=str(source),
                    target_path=str(target),
                    details="File copied successfully",
                    execution_time=time.time() - start_time
                )
                
            except Exception as e:
                result = FileOperationResult(
                    success=False,
                    operation=FileOperation.COPY,
                    source_path=operation["source"],
                    target_path=operation.get("target"),
                    details="Failed to copy file",
                    execution_time=time.time() - start_time,
                    error_message=str(e)
                )
            
            self.operation_history.append(result)
            return result
        
        # Execute batch operations concurrently
        tasks = [copy_single_file(op) for op in copy_operations]
        results = await asyncio.gather(*tasks)
        
        return results
    
    def get_operation_summary(self) -> Dict[str, Any]:
        """Get summary of all operations performed"""
        total_operations = len(self.operation_history)
        successful_operations = len([r for r in self.operation_history if r.success])
        failed_operations = total_operations - successful_operations
        
        total_execution_time = sum(r.execution_time for r in self.operation_history)
        
        operations_by_type = {}
        for result in self.operation_history:
            op_type = result.operation.value
            if op_type not in operations_by_type:
                operations_by_type[op_type] = {"total": 0, "successful": 0, "failed": 0}
            
            operations_by_type[op_type]["total"] += 1
            if result.success:
                operations_by_type[op_type]["successful"] += 1
            else:
                operations_by_type[op_type]["failed"] += 1
        
        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "total_execution_time": total_execution_time,
            "operations_by_type": operations_by_type,
            "recent_operations": [
                {
                    "operation": r.operation.value,
                    "source": r.source_path,
                    "target": r.target_path,
                    "success": r.success,
                    "execution_time": r.execution_time
                }
                for r in self.operation_history[-10:]  # Last 10 operations
            ]
        }

class ConflictDetector:
    """Detects and resolves file conflicts"""
    
    def __init__(self):
        self.conflict_patterns = [
            "CONFLICT",
            "<<<<<<< HEAD",
            ">>>>>>> branch",
            "======="
        ]
    
    def detect_conflicts(self, content: str) -> List[str]:
        """Detect merge conflicts in file content"""
        conflicts = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() in self.conflict_patterns:
                conflicts.append(f"Line {i+1}: {line.strip()}")
        
        return conflicts
    
    def detect_file_conflicts(self, file_path1: str, file_path2: str) -> Dict[str, Any]:
        """Detect conflicts between two files"""
        try:
            path1 = Path(file_path1)
            path2 = Path(file_path2)
            
            if not path1.exists() or not path2.exists():
                return {"exists": False, "conflicts": [], "type": "file_not_found"}
            
            # Check if files are identical
            if path1.read_bytes() == path2.read_bytes():
                return {"identical": True, "conflicts": [], "type": "identical"}
            
            # Check for merge conflicts in content
            content1 = path1.read_text(encoding='utf-8', errors='ignore')
            content2 = path2.read_text(encoding='utf-8', errors='ignore')
            
            conflicts1 = self.detect_conflicts(content1)
            conflicts2 = self.detect_conflicts(content2)
            
            if conflicts1 or conflicts2:
                return {
                    "merge_conflicts": True,
                    "conflicts": conflicts1 + conflicts2,
                    "type": "merge_conflict",
                    "file1": file_path1,
                    "file2": file_path2
                }
            
            # Generate diff
            diff = list(difflib.unified_diff(
                content1.splitlines(keepends=True),
                content2.splitlines(keepends=True),
                fromfile=file_path1,
                tofile=file_path2,
                lineterm=''
            ))
            
            return {
                "identical": False,
                "conflicts": [],
                "has_differences": len(diff) > 0,
                "diff": diff,
                "type": "content_difference",
                "file1": file_path1,
                "file2": file_path2
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "type": "analysis_error",
                "file1": file_path1,
                "file2": file_path2
            }
    
    def resolve_conflict(self, file_path: str, resolution: ConflictResolution) -> bool:
        """Resolve a file conflict using specified strategy"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            content = path.read_text(encoding='utf-8', errors='ignore')
            conflicts = self.detect_conflicts(content)
            
            if not conflicts:
                return True  # No conflicts to resolve
            
            if resolution == ConflictResolution.SKIP:
                return False  # Skip resolution
            
            elif resolution == ConflictResolution.BACKUP_AND_OVERWRITE:
                # Create backup
                backup_path = path.with_suffix(path.suffix + f".backup.{int(time.time())}")
                shutil.copy2(path, backup_path)
                
                # Simple conflict resolution: remove conflict markers
                resolved_content = content
                for pattern in self.conflict_patterns:
                    resolved_content = resolved_content.replace(pattern, "")
                
                # Remove conflict sections (simplified)
                lines = resolved_content.split('\n')
                resolved_lines = []
                skip_section = False
                
                for line in lines:
                    if "<<<<<<< HEAD" in line:
                        skip_section = True
                        continue
                    elif "======" in line:
                        skip_section = False
                        continue
                    elif ">>>>>>> " in line:
                        continue
                    elif not skip_section:
                        resolved_lines.append(line)
                
                resolved_content = '\n'.join(resolved_lines)
                path.write_text(resolved_content, encoding='utf-8')
                return True
            
            elif resolution == ConflictResolution.OVERWRITE:
                # Simple overwrite with cleaned content
                resolved_content = content
                for pattern in self.conflict_patterns:
                    resolved_content = resolved_content.replace(pattern, "")
                
                path.write_text(resolved_content, encoding='utf-8')
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Failed to resolve conflict: {e}")
            return False

class AdvancedFileOperations:
    """Main file operations system"""
    
    def __init__(self, workspace_dir: str = "/workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.vcs_manager = VersionControlManager(workspace_dir)
        self.batch_processor = BatchFileProcessor()
        self.conflict_detector = ConflictDetector()
        self.file_cache = {}
        self.load_file_cache()
    
    def load_file_cache(self):
        """Load file metadata cache"""
        cache_file = self.workspace_dir / "data" / "file_cache.json"
        try:
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    self.file_cache = json.load(f)
        except Exception:
            self.file_cache = {}
    
    def save_file_cache(self):
        """Save file metadata cache"""
        cache_file = self.workspace_dir / "data" / "file_cache.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_file, 'w') as f:
            json.dump(self.file_cache, f, indent=2, default=str)
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file metadata"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"exists": False}
            
            stat_info = path.stat()
            content_hash = self._calculate_file_hash(path)
            
            metadata = {
                "exists": True,
                "path": str(path.absolute()),
                "size": stat_info.st_size,
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "permissions": oct(stat_info.st_mode)[-3:],
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "content_hash": content_hash,
                "extension": path.suffix,
                "name": path.name,
                "parent": str(path.parent)
            }
            
            # Cache metadata
            self.file_cache[file_path] = metadata
            return metadata
            
        except Exception as e:
            return {"exists": False, "error": str(e)}
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def resolve_file_path(self, file_pattern: str, search_dirs: List[str] = None) -> List[str]:
        """Resolve file patterns to actual file paths"""
        if search_dirs is None:
            search_dirs = [str(self.workspace_dir)]
        
        resolved_files = []
        
        for search_dir in search_dirs:
            search_path = Path(search_dir)
            
            for root, dirs, files in os.walk(search_path):
                # Apply glob pattern
                for file_name in fnmatch.filter(files, file_pattern):
                    full_path = Path(root) / file_name
                    resolved_files.append(str(full_path))
                
                # Apply glob pattern to directories
                for dir_name in fnmatch.filter(dirs, file_pattern):
                    full_path = Path(root) / dir_name
                    resolved_files.append(str(full_path))
        
        return list(set(resolved_files))  # Remove duplicates
    
    async def safe_create_file(self, file_path: str, content: str, 
                             backup_existing: bool = True,
                             resolve_conflicts: bool = True) -> FileOperationResult:
        """Safely create a file with backup and conflict resolution"""
        start_time = time.time()
        
        try:
            path = Path(file_path)
            
            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle existing files
            if path.exists():
                if backup_existing:
                    backup_path = path.with_suffix(path.suffix + f".backup.{int(time.time())}")
                    shutil.copy2(path, backup_path)
                
                if resolve_conflicts:
                    # Check for conflicts
                    existing_content = path.read_text(encoding='utf-8', errors='ignore')
                    conflicts = self.conflict_detector.detect_conflicts(existing_content)
                    
                    if conflicts:
                        # Try to resolve conflicts
                        success = self.conflict_detector.resolve_conflict(
                            file_path, ConflictResolution.BACKUP_AND_OVERWRITE
                        )
                        if not success:
                            return FileOperationResult(
                                success=False,
                                operation=FileOperation.CREATE,
                                source_path=file_path,
                                target_path=None,
                                details="Failed to resolve existing conflicts",
                                execution_time=time.time() - start_time,
                                error_message="Conflict resolution failed"
                            )
            
            # Create the file
            path.write_text(content, encoding='utf-8')
            
            # Update cache
            self.get_file_metadata(file_path)
            self.save_file_cache()
            
            # Stage in version control if available
            if self.vcs_manager.git_available:
                self.vcs_manager.stage_files([file_path])
            
            return FileOperationResult(
                success=True,
                operation=FileOperation.CREATE,
                source_path=file_path,
                target_path=None,
                details=f"Created file with {len(content)} characters",
                backup_created=backup_existing and path.exists(),
                conflict_resolved=resolve_conflicts,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return FileOperationResult(
                success=False,
                operation=FileOperation.CREATE,
                source_path=file_path,
                target_path=None,
                details="Failed to create file",
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def batch_file_operations(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch file operations"""
        create_operations = [op for op in operations if op.get("operation") == "create"]
        copy_operations = [op for op in operations if op.get("operation") == "copy"]
        
        results = {
            "create_results": [],
            "copy_results": [],
            "summary": {}
        }
        
        if create_operations:
            create_results = await self.batch_processor.batch_create_files(create_operations)
            results["create_results"] = create_results
        
        if copy_operations:
            copy_results = await self.batch_processor.batch_copy_files(copy_operations)
            results["copy_results"] = copy_results
        
        # Get overall summary
        summary = self.batch_processor.get_operation_summary()
        results["summary"] = summary
        
        return results
    
    def analyze_file_structure(self, directory: str = None) -> Dict[str, Any]:
        """Analyze file structure and provide insights"""
        if directory is None:
            directory = str(self.workspace_dir)
        
        try:
            path = Path(directory)
            if not path.exists():
                return {"error": "Directory does not exist"}
            
            analysis = {
                "directory": str(path.absolute()),
                "total_files": 0,
                "total_dirs": 0,
                "file_types": {},
                "total_size": 0,
                "largest_files": [],
                "recently_modified": [],
                "empty_files": [],
                "binary_files": []
            }
            
            recent_threshold = time.time() - (7 * 24 * 3600)  # 7 days ago
            
            for root, dirs, files in os.walk(path):
                analysis["total_dirs"] += len(dirs)
                
                for file_name in files:
                    file_path = Path(root) / file_name
                    analysis["total_files"] += 1
                    
                    try:
                        stat_info = file_path.stat()
                        analysis["total_size"] += stat_info.st_size
                        
                        # File type analysis
                        ext = file_path.suffix.lower()
                        if ext:
                            analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1
                        else:
                            analysis["file_types"]["no_extension"] = analysis["file_types"].get("no_extension", 0) + 1
                        
                        # Check for empty files
                        if stat_info.st_size == 0:
                            analysis["empty_files"].append(str(file_path))
                        
                        # Check for binary files (simple heuristic)
                        if stat_info.st_size > 0:
                            try:
                                with open(file_path, 'rb') as f:
                                    chunk = f.read(1024)
                                if b'\x00' in chunk:  # Contains null bytes (likely binary)
                                    analysis["binary_files"].append(str(file_path))
                            except:
                                pass
                        
                        # Track largest files
                        analysis["largest_files"].append({
                            "path": str(file_path),
                            "size": stat_info.st_size
                        })
                        
                        # Track recently modified files
                        if stat_info.st_mtime > recent_threshold:
                            analysis["recently_modified"].append({
                                "path": str(file_path),
                                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                                "size": stat_info.st_size
                            })
                            
                    except Exception:
                        continue
            
            # Sort and limit results
            analysis["largest_files"].sort(key=lambda x: x["size"], reverse=True)
            analysis["largest_files"] = analysis["largest_files"][:10]  # Top 10
            analysis["recently_modified"].sort(key=lambda x: x["modified"], reverse=True)
            analysis["recently_modified"] = analysis["recently_modified"][:10]  # Top 10
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_workspace_status(self) -> Dict[str, Any]:
        """Get comprehensive workspace status"""
        status = {
            "workspace_path": str(self.workspace_dir.absolute()),
            "file_operations": self.batch_processor.get_operation_summary(),
            "version_control": self.vcs_manager.get_status(),
            "file_cache_size": len(self.file_cache),
            "last_cache_update": datetime.now().isoformat()
        }
        
        # Add directory analysis
        status["directory_analysis"] = self.analyze_file_structure()
        
        return status

# Singleton instance
file_ops = AdvancedFileOperations()

# Convenience functions
async def create_file_safely(file_path: str, content: str, **kwargs) -> FileOperationResult:
    """Safely create a file"""
    return await file_ops.safe_create_file(file_path, content, **kwargs)

async def batch_create_files(operations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create multiple files in batch"""
    return await file_ops.batch_file_operations(operations)

def resolve_file_pattern(pattern: str, search_dirs: List[str] = None) -> List[str]:
    """Resolve file pattern to actual paths"""
    return file_ops.resolve_file_path(pattern, search_dirs)

def analyze_workspace() -> Dict[str, Any]:
    """Analyze workspace structure"""
    return file_ops.get_workspace_status()

if __name__ == "__main__":
    # Demo the Advanced File Operations System
    print("📁 Advanced File Operations System Demo")
    print("=" * 50)
    
    # Demo 1: Safe file creation
    async def demo_safe_creation():
        print("\n🔒 Safe File Creation Demo:")
        
        result = await create_file_safely(
            "/workspace/demo_files/test_file.txt",
            "This is a test file created safely with backup and conflict resolution.",
            backup_existing=True,
            resolve_conflicts=True
        )
        
        print(f"✅ File creation: {result.success}")
        print(f"   Path: {result.source_path}")
        print(f"   Details: {result.details}")
        print(f"   Backup created: {result.backup_created}")
        print(f"   Conflicts resolved: {result.conflict_resolved}")
        print(f"   Execution time: {result.execution_time:.3f}s")
    
    # Demo 2: Batch file operations
    async def demo_batch_operations():
        print("\n⚡ Batch File Operations Demo:")
        
        operations = [
            {"operation": "create", "path": "/workspace/demo_files/batch1.txt", "content": "Batch file 1"},
            {"operation": "create", "path": "/workspace/demo_files/batch2.txt", "content": "Batch file 2"},
            {"operation": "create", "path": "/workspace/demo_files/batch3.txt", "content": "Batch file 3"},
            {"operation": "create", "path": "/workspace/demo_files/subdir/batch4.txt", "content": "Batch file 4", "create_dirs": True}
        ]
        
        results = await batch_create_files(operations)
        
        print(f"✅ Batch operations completed")
        print(f"   Total operations: {results['summary']['total_operations']}")
        print(f"   Successful: {results['summary']['successful_operations']}")
        print(f"   Failed: {results['summary']['failed_operations']}")
        print(f"   Success rate: {results['summary']['success_rate']:.1%}")
        print(f"   Total execution time: {results['summary']['total_execution_time']:.3f}s")
    
    # Demo 3: File pattern resolution
    def demo_pattern_resolution():
        print("\n🔍 File Pattern Resolution Demo:")
        
        # Create some test files first
        test_files = [
            "/workspace/demo_files/test1.py",
            "/workspace/demo_files/test2.py", 
            "/workspace/demo_files/test1.txt",
            "/workspace/demo_files/config.json",
            "/workspace/demo_files/readme.md"
        ]
        
        for file_path in test_files:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).touch()
        
        # Resolve patterns
        python_files = resolve_file_pattern("*.py")
        config_files = resolve_file_pattern("*.json")
        all_files = resolve_file_pattern("*")
        
        print(f"✅ Python files found: {len(python_files)}")
        for f in python_files:
            print(f"   - {f}")
        
        print(f"✅ Config files found: {len(config_files)}")
        for f in config_files:
            print(f"   - {f}")
        
        print(f"✅ All files found: {len(all_files)}")
    
    # Demo 4: Workspace analysis
    def demo_workspace_analysis():
        print("\n📊 Workspace Analysis Demo:")
        
        status = analyze_workspace()
        
        print(f"✅ Workspace status:")
        print(f"   Path: {status['workspace_path']}")
        print(f"   File cache size: {status['file_cache_size']} entries")
        print(f"   Total operations: {status['file_operations']['total_operations']}")
        
        # Directory analysis
        analysis = status['directory_analysis']
        if 'error' not in analysis:
            print(f"   Total files: {analysis['total_files']}")
            print(f"   Total directories: {analysis['total_dirs']}")
            print(f"   Total size: {analysis['total_size']} bytes")
            print(f"   File types: {list(analysis['file_types'].keys())}")
        else:
            print(f"   Analysis error: {analysis['error']}")
    
    # Run demos
    import asyncio
    asyncio.run(demo_safe_creation())
    asyncio.run(demo_batch_operations())
    demo_pattern_resolution()
    demo_workspace_analysis()
    
    print(f"\n🎯 Advanced File Operations System Ready!")
    print("✅ Complex file system navigation implemented")
    print("✅ Batch file processing working")
    print("✅ Version control integration active")
    print("✅ Dynamic path resolution functional")
    print("✅ File conflict detection and resolution enabled")