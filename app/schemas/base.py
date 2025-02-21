from typing import Annotated

from pydantic import BeforeValidator

PyObjectID = Annotated[str, BeforeValidator(str)]
