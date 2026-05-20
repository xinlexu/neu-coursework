import org.junit.Before;
import org.junit.Test;
import static org.junit.Assert.*;

public class EngineerImpTest {
    private JuniorSDE junior;
    private SDE sde;
    private SeniorSDE senior;

    @Before
    public void setUp() {
        junior = new JuniorSDE("Alice", 1000.0, 200);
        sde = new SDE("Bob", 1200.0, 300, 5);
        senior = new SeniorSDE("Charlie", 1500.0, 10);
    }

    @Test
    public void testJuniorSDE_GetName() {
        assertEquals("Alice", junior.getName());
    }

    @Test
    public void testJuniorSDE_SetBonus_MEET_EXPECTATION() {
        junior.setBonus(Rating.MEET_EXPECTATION);
        double expectedBonus = junior.computeBaseBonus() * (200 / 100.0);
        assertEquals(expectedBonus, junior.getBonus(), 0.001);
    }

    @Test
    public void testJuniorSDE_SetBonus_SUPERB() {
        junior.setBonus(Rating.SUPERB);
        double expectedBonus = junior.computeBaseBonus() * (200 / 100.0) * 2.0;
        assertEquals(expectedBonus, junior.getBonus(), 0.001);
    }

    @Test
    public void testSDE_GetName() {
        assertEquals("Bob", sde.getName());
    }

    @Test
    public void testSDE_SetBonus_EXCEED_EXPECTATION() {
        sde.setBonus(Rating.EXCEED_EXPECTATION);
        double expectedBonus = sde.computeBaseBonus() * ((300 / 80.0) + (5 / 5.0)) * 1.2;
        assertEquals(expectedBonus, sde.getBonus(), 0.001);
    }

    @Test
    public void testSDE_SetBonus_SUPERB() {
        sde.setBonus(Rating.SUPERB);
        double expectedBonus = sde.computeBaseBonus() * ((300 / 80.0) + (5 / 5.0)) * 1.7;
        assertEquals(expectedBonus, sde.getBonus(), 0.001);
    }

    @Test
    public void testSeniorSDE_GetName() {
        assertEquals("Charlie", senior.getName());
    }

    @Test
    public void testSeniorSDE_SetBonus_EXCEED_EXPECTATION() {
        senior.setBonus(Rating.EXCEED_EXPECTATION);
        double expectedBonus = senior.computeBaseBonus() * (10 / 5.0);
        assertEquals(expectedBonus, senior.getBonus(), 0.001);
    }

    @Test
    public void testSeniorSDE_SetBonus_SUPERB() {
        senior.setBonus(Rating.SUPERB);
        double expectedBonus = senior.computeBaseBonus() * (10 / 5.0);
        assertEquals(expectedBonus, senior.getBonus(), 0.001);
    }
}
