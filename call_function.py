from google.genai import types
from config import WORKING_DIR
from get_files_info import get_files_info, schema_get_files_info
from get_file_content import get_file_content, schema_get_file_content
from write_file import write_file, schema_write_file
from run_python import run_python_file, schema_run_python_file


available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_write_file,
        schema_run_python_file,
    ]
)

FUNCTION_MAP = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "write_file": write_file,
    "run_python_file": run_python_file,
}


def call_function(function_call_part, verbose=False):
    name = function_call_part.name
    if verbose:
        print(f" - Calling function: {name}({dict(function_call_part.args)})")
    else:
        print(f" - Calling: {name}")

    if name not in FUNCTION_MAP:
        response = {"error": f"Unknown function: {name}"}
    else:
        args = dict(function_call_part.args)
        args["working_directory"] = WORKING_DIR
        try:
            result = FUNCTION_MAP[name](**args)
            response = {"result": result}
        except Exception as e:
            response = {"error": str(e)}

    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(name=name, response=response)
        ],
    )
