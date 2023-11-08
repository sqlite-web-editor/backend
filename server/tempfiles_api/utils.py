from typing import Dict, Any, List


def fix_strings_in_sql(string: str):
    return f'"{string}"'


def conclude_in_brackets(string: str) -> str:
    return f"({string})"
    

def detect_sql_string(any: Any):
    if isinstance(any, str):
        return fix_strings_in_sql(any)
        
    return str(any)


def get_sql_equal_expression(values: Dict[str, Any]) -> List[str]:
    return [f"{name}={detect_sql_string(value)}" if value is not None else f"{name} IS NULL" for name, value in values.items()]


def get_where_expression(values: Dict[str, Any]) -> str:
    """
    return str with sql where expression by given values - name: value
    get_where_expression({"id": 1, "money": 200}) -> WHERE id=1 AND money=200
    
    """
    return "WHERE "+" AND ".join([f'{item} = ?' for item in values.keys()])


def get_set_expression(values: Dict[str, Any]) -> str:
    return "SET "+", ".join([f'{item} = ?' for item in values.keys()])


def get_sql_values_expression(values: Dict[str, Any]) -> str:
    
    columns: str = conclude_in_brackets(", ".join(values.keys()))
    values_expression: str = "VALUES "+conclude_in_brackets(",".join(["?" for _ in values.items()]))
    
    return f"{columns} {values_expression}"
