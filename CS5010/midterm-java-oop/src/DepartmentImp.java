import java.util.Iterator;
import java.util.function.Predicate;

public class DepartmentImp implements Department {
    private static DepartmentImp instance = null;

    private static final int MAX_ENGINEERS_PER_TEAM = 3;
    private static final int NUM_TEAMS = 4;
    private final OrderedListImp<Engineer>[] teams =
            (OrderedListImp<Engineer>[]) new OrderedListImp[NUM_TEAMS];

    private DepartmentImp() {
        for (int i = 0; i < NUM_TEAMS; i++) {
            teams[i] = new OrderedListImp<>();
        }
    }

    public void clear() {
        for (int i = 0; i < NUM_TEAMS; i++) {
            teams[i] = new OrderedListImp<>(); // 初始化每个团队
        }
    }

    public static DepartmentImp getInstance() {
        if (instance == null) {
            instance = new DepartmentImp();
        }
        return instance;
    }

    @Override
    public boolean hire(Engineer e, int teamId) {
        if (teamId < 0 || teamId >= NUM_TEAMS) {
            throw new IndexOutOfBoundsException("Wrong team id");
        }
        OrderedListImp<Engineer> team = teams[teamId];
        if (team.size() >= MAX_ENGINEERS_PER_TEAM) {
            return false;
        }
        team.add(e);
        return true;
    }

    @Override
    public void giveOutBonus() {
        for (OrderedListImp<Engineer> team : teams) {
            for (Engineer engineer : team) {
                engineer.setBonus(Rating.EXCEED_EXPECTATION);
            }
        }
    }

    @Override
    public void layoff(double bonusThreshold) {
        for (int i = 0; i < teams.length; i++) {
            OrderedListImp<Engineer> team = teams[i];
            Predicate<Engineer> predicate = engineer -> engineer.getBonus() >= bonusThreshold;
            teams[i] = team.subList(predicate);
        }
    }

    @Override
    public Iterator<Engineer> iterator() {
        return new DepartmentIterator();
    }

    private class DepartmentIterator implements Iterator<Engineer> {
        private int teamIndex = 0;
        private Iterator<Engineer> currentTeamIterator = teams[0].iterator();

        @Override
        public boolean hasNext() {
            while (teamIndex < NUM_TEAMS) {
                if (currentTeamIterator.hasNext()) {
                    return true;
                }
                teamIndex++;
                if (teamIndex < NUM_TEAMS) {
                    currentTeamIterator = teams[teamIndex].iterator();
                }
            }
            return false;
        }

        @Override
        public Engineer next() {
            return currentTeamIterator.next();
        }
    }
}
