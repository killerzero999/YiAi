import YiDate



class YiJingClass:
    def __init__(self, name, value):
        print(f"Creating {name}")
        self.name = name
        self.value = value
        self.YI_GUA_BIN_ORDER_LIST = YiDate.YiIntList

    def __str__(self):
        return f"{self.name}: {self.value}"

    def __del__(self):
        print(f"Deleting {self.name}")

    def get_yi_gua_bin_order_list(self):
        return self.YI_GUA_BIN_ORDER_LIST