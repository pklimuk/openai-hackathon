
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd


if __name__ == "__main__":
    # Sample data: Adjust these values as needed

    years = [2025, 2026, 2027, 2028, 2029, 2030]
    market_sizes = [1.3]
    for _ in years[1:]:
        market_sizes.append(market_sizes[-1] * 1.045)

    data = {
        "Year": years,
        "Market Size (Trillion USD)": market_sizes
    }

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Set up the plot with dark theme
    plt.style.use("dark_background")
    plt.figure(figsize=(12, 7))
    
    # Create a bar plot with custom colors
    bar_plot = sns.barplot(x="Year", y="Market Size (Trillion USD)", data=df, 
                          palette=sns.color_palette("crest", len(years)))
    
    # Enhance the plot with styling
    plt.gcf().set_facecolor("#212121")
    plt.gca().set_facecolor("#212121")
    
    # Add a subtle grid for readability
    plt.grid(axis="y", linestyle="--", alpha=0.3)
    
    # Style the labels and title
    bar_plot.set_xlabel("Year", fontsize=14, color="#FFFFFF")
    bar_plot.set_ylabel("Market Size (Trillion USD)", fontsize=14, color="#FFFFFF")
    bar_plot.set_xticklabels(bar_plot.get_xticklabels(), rotation=45, color="#FFFFFF")
    bar_plot.set_yticklabels([f"${x:.2f}T" for x in bar_plot.get_yticks()], color="#FFFFFF")
    
    # Add value labels on top of each bar
    for i, bar in enumerate(bar_plot.patches):
        bar_plot.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.02,
            f"${market_sizes[i]:.2f}T",
            ha="center", color="#FFFFFF", fontweight="bold"
        )
    
    # Title with custom styling
    plt.title("Forecast of the Market Size of Education in US", 
              fontsize=18, color="#FFFFFF", fontweight="bold", pad=20)
    
    # Add a subtle border around the plot
    for spine in plt.gca().spines.values():
        spine.set_edgecolor("#333333")
    
    # Adjust layout for better spacing
    plt.tight_layout()
    
    # Show plot
    # plt.show()

    # Save the plot
    plt.savefig("education_market_size.png", dpi=300)
