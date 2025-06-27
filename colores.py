import matplotlib.pyplot as plt

# Define color mappings
colors = {
    "metro_ligero": {
        "1": "#70C5E8",
    "2": "#9B4782",
    "3": "#DE1E40"
    },
    "cercanias": {
        "C-1":  "#70C5E8",
        "C-2":  "#008F3E",
        "C-3":  "#9B4782",
        "C-4a": "#004E98",
        "C-4b": "#004E98",
        "C-5":  "#F2C500",
        "C-7":  "#DE1E40",
        "C-8":  "#808080",
        "C-8a": "#B2B2B2",
        "C-9":  "#F09600",
        "C-10": "#B0D136"
    },
    "metro": {
        "1":  "#30A3DC",
        "2":  "#E0292F",
        "3":  "#FFE114",
        "4":  "#814109",
        "5":  "#96BF0D",
        "6":  "#9A9999",
        "7":  "#F96611",
        "8":  "#F373B7",
        "9":  "#990D66",
        "10": "#1B0C80",
        "11": "#136926",
        "12": "#999933",
        "R":  "#800080"
    }
}

# Function to plot color swatches
def plot_swatches(category, mapping):
    labels = list(mapping.keys())
    hex_values = list(mapping.values())
    plt.figure(figsize=(8, len(labels) * 0.5))
    for idx, (label, color) in enumerate(zip(labels, hex_values)):
        plt.barh(idx, 1, color=color)
    plt.yticks(range(len(labels)), labels)
    plt.xticks([])
    plt.title(f"{category.replace('_', ' ').title()} Colors")
    plt.tight_layout()
    plt.show()

# Plot each category
for cat, mapping in colors.items():
    plot_swatches(cat, mapping)
