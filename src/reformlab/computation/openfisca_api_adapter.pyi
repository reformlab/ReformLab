from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

class OpenFiscaApiAdapter:
    def __init__(
        self,
        *,
        country_package: str = ...,
        output_variables: tuple[str, ...],
        skip_version_check: bool = ...,
    ) -> None: ...
    def version(self) -> str: ...
    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult: ...
