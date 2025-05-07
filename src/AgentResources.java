import java.util.EnumMap;
import java.util.Map;

public class AgentResources {
    private final Map<PathColor, Integer> cards;

    public AgentResources() {
        cards = new EnumMap<>(PathColor.class);
        // Initialize all values to 0
        for (PathColor color : PathColor.values()) {
            cards.put(color, 0);
        }
    }

    public int getCards(PathColor color) {
        return cards.getOrDefault(color, 0);
    }

    public void setCards(PathColor color, int number) {
        cards.put(color, number);
    }

    public void addCards(PathColor color, int amount) {
        cards.put(color, getCards(color) + amount);
    }

    public void removeCards(PathColor color, int amount) {
        cards.put(color, Math.max(0, getCards(color) - amount));
    }
}