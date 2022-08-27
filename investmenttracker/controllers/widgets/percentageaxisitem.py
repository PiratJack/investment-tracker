"""A class to display axis item value as percentage

Classes
----------
PercentageAxisItem
    A class to display axis item value as percentage
"""
import pyqtgraph


class PercentageAxisItem(pyqtgraph.AxisItem):
    def tickStrings(self, values, scale, spacing):
        if self.logMode:
            return super().tickStrings(values, scale, spacing)

        if any(value * scale > 3 for value in values):
            return super().tickStrings(values, scale, spacing)

        strings = []
        for value in values:
            value_scaled = value * scale
            value_label = f"{value_scaled:.1%}"
            strings.append(value_label)
        return strings
