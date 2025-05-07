import jade.core.Agent;

public class ColorTrailAgent extends Agent {
    private Environment env;
    private int x, y;
    public Cell position;
    private AgentResources resources;
    @Override
    protected void setup() {
        Object[] args = getArguments();
        if (args != null && args.length >= 2) {
            env = (Environment) args[0];
            position = env.getRandomInitialCell();
            resources = (AgentResources) args[1];
            System.out.println(getLocalName() + " started at position (" + position.x + ", " + position.y + ")");
            System.out.println("Path color here: " + position.color);
        } else {
            System.out.println("Missing arguments for " + getLocalName());
            doDelete(); // terminate the agent
        }
    }
}
