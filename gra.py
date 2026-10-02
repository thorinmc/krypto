def shift_x_by_1920(coord_str, dx=1920):
    # Usuwamy spacje i dzielimy po przecinku
    parts = [p.strip() for p in coord_str.split(",") if p.strip() != ""]

    # Zamiana na liczby (o ile się da)
    nums = [int(p) for p in parts]

    # Zależnie od ilości liczb traktujemy to jako:
    # 1 liczba: x
    # 2 liczby: x, y
    # 4 liczby: x1, y1, x2, y2
    # Jeśli inna ilość – po prostu przesuwamy wszystkie "parzyste" indeksy (0, 2, 4...) jako X
    for i in range(0, len(nums), 2):
        nums[i] += dx

    # Składamy z powrotem do stringa
    return ", ".join(str(n) for n in nums)


# PRZYKŁADY UŻYCIA:
#print(shift_x_by_1920("-340, 805, -275, 840"))  # -> 460, 90, 754, 110
#print(shift_x_by_1920("-340, 160"))              # -> 1489, 300
print(shift_x_by_1920(""))     