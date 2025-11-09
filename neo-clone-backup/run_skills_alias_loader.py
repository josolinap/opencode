# Alias-loader: force the intended skills package to be registered under the name 'skills'
# so that submodule imports like `from skills import ...` inside skill modules
# bind to this package and can register into its registry.
import os
import sys
import logging
import importlib
import importlib.util
import traceback

logging.basicConfig(level=logging.INFO, format="%(message)s")
ROOT = "/app/neo_tui_assistant_1544/neo-clone"
SKILLS_DIR = os.path.join(ROOT, "skills")
SKILLS_INIT = os.path.join(SKILLS_DIR, "__init__.py")

def load_package_as_skills(path_init: str, package_name: str = "skills"):
    """
    Load the file at path_init as a package module and insert it into sys.modules
    under the name package_name. Sets __path__ to the skills directory so
    imports like 'skills.<sub>' work.
    """
    try:
        logging.info("Loading skills package from %s as '%s'", path_init, package_name)
        spec = importlib.util.spec_from_file_location(package_name, path_init)
        if spec is None:
            raise ImportError(f"Could not create spec for {path_init}")
        module = importlib.util.module_from_spec(spec)
        # set package __path__ so that imports of submodules work (PEP 328)
        module.__path__ = [os.path.abspath(os.path.dirname(path_init))]
        # register in sys.modules before execution to allow relative imports inside __init__
        sys.modules[package_name] = module
        loader = spec.loader
        if loader is None:
            raise ImportError("No loader for spec")
        loader.exec_module(module)
        logging.info("Loaded package '%s' from %s (module file: %s)", package_name, path_init, getattr(module, "__file__", None))
        return module
    except Exception as e:
        logging.error("Failed to load package %s: %s", package_name, e)
        traceback.print_exc()
        raise

def import_skill_submodules(package_name: str = "skills"):
    """
    Import each .py file in SKILLS_DIR (except __init__.py) as submodule under package_name.
    """
    imported = []
    for fname in sorted(os.listdir(SKILLS_DIR)):
        if not fname.endswith(".py"):
            continue
        if fname == "__init__.py":
            continue
        mod_name = os.path.splitext(fname)[0]
        full_name = f"{package_name}.{mod_name}"
        try:
            logging.info("Importing submodule %s", full_name)
            # Using import_module so that proper package semantics used
            mod = importlib.import_module(full_name)
            logging.info("Imported %s -> file: %s", full_name, getattr(mod, "__file__", None))
            imported.append(full_name)
        except Exception as e:
            logging.error("Failed to import %s: %s", full_name, e)
            traceback.print_exc()
    return imported

def find_registry(pkg_module):
    """
    Heuristically find a registry object on the package module.
    """
    # Common names
    for name in ("DEFAULT_REGISTRY", "registry", "skill_registry", "SKILL_REGISTRY"):
        if hasattr(pkg_module, name):
            return getattr(pkg_module, name), name
    # Search for objects with methods list_skills and execute_skill
    for k, v in vars(pkg_module).items():
        if hasattr(v, "list_skills") and hasattr(v, "execute_skill"):
            return v, k
    return None, None

def main():
    try:
        if not os.path.exists(SKILLS_INIT):
            logging.error("Skills __init__.py not found at %s", SKILLS_INIT)
            sys.exit(2)

        # Ensure our project root is first in sys.path to reduce accidental shadowing
        proj_root = os.path.abspath(ROOT)
        if proj_root in sys.path:
            sys.path.remove(proj_root)
        sys.path.insert(0, proj_root)
        logging.info("Prepended project root to sys.path: %s", proj_root)
        logging.info("sys.path[0:5]=%s", sys.path[:5])

        # Load skills package as 'skills' (alias)
        pkg = load_package_as_skills(SKILLS_INIT, "skills")

        # Show initial members
        logging.info("skills module members (post-load): %s", sorted(k for k in dir(pkg) if not k.startswith("_")))

        # Import submodules under skills.*
        imported = import_skill_submodules("skills")
        logging.info("Imported submodules: %s", imported)

        # Inspect sys.modules relevant entries
        related = [k for k in sys.modules.keys() if k == "skills" or k.startswith("skills.")]
        logging.info("Relevant sys.modules entries: %s", related)

        # Try to find registry on package
        registry, reg_name = find_registry(pkg)
        if registry is None:
            logging.warning("No registry attribute found on skills package after imports. Dumping module globals for inspection:")
            for k, v in list(vars(pkg).items()):
                logging.info(" - %s: %s", k, type(v))
        else:
            logging.info("Located registry attribute: %s -> %s", reg_name, registry)

            # List skills
            try:
                skills = registry.list_skills()
                logging.info("Registered skills: %s", skills)
                # Run smoke execute on each skill
                for s in skills:
                    logging.info("Executing smoke test for skill: %s", s)
                    try:
                        out = registry.execute_skill(s, {})
                        logging.info("Smoke output for %s: %s", s, repr(out))
                    except Exception as e:
                        logging.error("Error executing skill %s: %s", s, e)
                        traceback.print_exc()
            except Exception as e:
                logging.error("Error interacting with registry: %s", e)
                traceback.print_exc()

        logging.info("Done.")
    except Exception as e:
        logging.error("Fatal error: %s", e)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()