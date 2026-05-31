from composition_engine.schema import Composition


def composition_to_dict(composition: Composition) -> dict:
    return composition.model_dump(by_alias=True)


def composition_from_dict(data: dict) -> Composition:
    return Composition.model_validate(data)


def composition_to_json(composition: Composition) -> str:
    return composition.model_dump_json(by_alias=True)


def composition_from_json(json_str: str) -> Composition:
    return Composition.model_validate_json(json_str)
