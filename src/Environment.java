public class Environment {
    public static final int WIDTH = 7;
    public static final int HEIGHT = 5;
    private final Cell[][] grid = new Cell[WIDTH][HEIGHT];

    public Environment() {
        initializeGrid();
    }

    private void initializeGrid() {
        PathColor[] colors = PathColor.values();
        for (int x = 0; x < WIDTH; x++) {
            for (int y = 0; y < HEIGHT; y++) {
                PathColor color = colors[(x + y) % colors.length];
                grid[x][y] = new Cell(x, y, color);
            }
        }
    }

    public Cell getCell(int x, int y) {
        if (x >= 0 && x < WIDTH && y >= 0 && y < HEIGHT) {
            return grid[x][y];
        }
        return null;
    }
}
