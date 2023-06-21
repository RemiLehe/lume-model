from typing import Dict, List

import torch

from lume_model.torch import PyTorchModel


class LUMEModule(torch.nn.Module):
    """Wrapper to allow a LUME PyTorchModel to be used as a torch Module.

    As the model within the PyTorchModel is assumed to be fixed during instantiation,
    so is the LUMEModule. Gradient computation can be retained by setting the fixed_model
    flag to False when creating the PyTorchModel.
    """

    def __init__(
        self,
        model: PyTorchModel,
        feature_order: List[str] = [],
        output_order: List[str] = [],
    ):
        """Initializes the model, and the order the features and outputs are passed.

        Args:
            model: Representation of the model.
            feature_order: List of feature names in the order they are passed to the model.
            output_order: List of output names in the order they are returned by the model.
        """
        super().__init__()
        self._model = model
        self._feature_order = feature_order
        self._output_order = output_order
        self.register_module("base_model", self._model.model)

    @property
    def feature_order(self):
        return self._feature_order

    @property
    def output_order(self):
        return self._output_order

    def evaluate_model(self, x: Dict[str, torch.Tensor]):
        """Placeholder method to modify model calls."""
        return self._model.evaluate(x)

    def manipulate_outcome(self, y_model: Dict[str, torch.Tensor]):
        """Placeholder method to modify the outcome of the model calls."""
        return y_model

    def forward(self, x: torch.Tensor):
        # incoming tensor will be of the shape [b,n,m] where b is the batch number,
        # n is the number of samples and m is the number of features we need to break up
        # this tensor into a dictionary format that the PyTorchModel will accept
        x = self._validate_input(x)
        model_input = self._tensor_to_dictionary(x)
        # evaluate model
        y_model = self.evaluate_model(model_input)
        y_model = self.manipulate_outcome(y_model)
        # then once we have the model output in dictionary format we convert
        # it back to a tensor for botorch
        y = self._dictionary_to_tensor(y_model).squeeze()
        return y

    def _tensor_to_dictionary(self, x: torch.Tensor):
        input_dict = {}
        for idx, feature in enumerate(self._feature_order):
            input_dict[feature] = x[..., idx].unsqueeze(-1)  # index by the last dimension
        return input_dict

    def _dictionary_to_tensor(self, y_model: Dict[str, torch.Tensor]):
        output_tensor = torch.stack(
            [y_model[outcome].unsqueeze(-1) for outcome in self._output_order], dim=-1
        )
        return output_tensor.squeeze()

    def _validate_input(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() <= 1:
            raise ValueError(
                f"""Expected input dim to be at least 2 ([n_samples, n_features]), 
                received: {tuple(x.shape)}"""
            )
        else:
            return x
