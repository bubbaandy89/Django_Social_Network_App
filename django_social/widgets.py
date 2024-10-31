from typing import Any, Dict

from django.forms import DateTimeInput


class BootstrapDateTimePickerInput(DateTimeInput):
    template_name = "widgets/bootstrap_datetimepicker.html"

    def get_context(self, name, value, attrs) -> Dict[str, Any]:
        datetimepicker_id: str = f"datetimepicker_{name}"
        if attrs is None:
            attrs = dict()
        attrs["data-target"] = f"#{datetimepicker_id}"
        attrs["class"] = "form-control datetimepicker-input"
        context: Dict[str, Any] = super().get_context(name, value, attrs)
        context["widget"]["datetimepicker_id"] = datetimepicker_id
        return context
