import java.util.ArrayList;

public class Environment {
    public static final int WIDTH = 7;
    public static final int HEIGHT = 5;
    private final Cell[][] grid = new Cell[WIDTH][HEIGHT];
    private ArrayList<Cell> freeCells = new ArrayList<>(WIDTH * HEIGHT);
    private ArrayList<Cell> occupiedCells = new ArrayList<>();
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
        for (int x = 0; x < WIDTH * HEIGHT; x++) {
            freeCells.add(x,grid[x / HEIGHT][x % WIDTH]);
        }
    }

    public Cell getRandomInitialCell(){
        int randomNum = (int)(Math.random() * freeCells.size());
        Cell cell = freeCells.get(randomNum);
        occupiedCells.add(cell);
        freeCells.remove(randomNum);
        return cell;
    }

    public Cell occupyCell(int x, int y) {
        Cell cell = getCell(x, y);
        occupiedCells.add(cell);
        freeCells.remove(x * WIDTH + y);
        return cell;
    }

    public Cell freeCell(int x, int y) {
        Cell cell = getCell(x, y);
        freeCells.add(cell);
        occupiedCells.remove(cell);
        return cell;
    }

    public Cell getCell(int x, int y) {
        if (x >= 0 && x < WIDTH && y >= 0 && y < HEIGHT) {
            return grid[x][y];
        }
        return null;
    }
}
