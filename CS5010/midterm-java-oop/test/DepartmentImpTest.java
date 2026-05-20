import org.junit.Before;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.Iterator;

public class DepartmentImpTest {
    private DepartmentImp department;

    @Before
    public void setUp() {
        department = DepartmentImp.getInstance();
    }

    @Test
    public void testHire() {
        JuniorSDE junior = new JuniorSDE("Alice", 1000.0, 200);
        SDE sde = new SDE("Bob", 1200.0, 300, 5);
        SeniorSDE senior = new SeniorSDE("Charlie", 1500.0, 10);

        assertTrue(department.hire(junior, 0));
        assertTrue(department.hire(sde, 0));
        assertTrue(department.hire(senior, 0));

        JuniorSDE junior2 = new JuniorSDE("David", 1000.0, 150);
        assertFalse(department.hire(junior2, 0));
    }

    @Test
    public void testGiveOutBonus() {
        JuniorSDE junior = new JuniorSDE("Alice", 1000.0, 200);
        SDE sde = new SDE("Bob", 1200.0, 300, 5);
        SeniorSDE senior = new SeniorSDE("Charlie", 1500.0, 10);

        department.hire(junior, 1);
        department.hire(sde, 1);
        department.hire(senior, 1);

        department.giveOutBonus();

        double expectedJuniorBonus = junior.computeBaseBonus() * (200 / 100.0);
        assertEquals(expectedJuniorBonus, junior.getBonus(), 0.001);

        double expectedSDEBonus = sde.computeBaseBonus() * ((300 / 80.0) + (5 / 5.0)) * 1.2;
        assertEquals(expectedSDEBonus, sde.getBonus(), 0.001);

        double expectedSeniorBonus = senior.computeBaseBonus() * (10 / 5.0);
        assertEquals(expectedSeniorBonus, senior.getBonus(), 0.001);
    }

    @Test
    public void testLayoff() {
        department.clear();

        JuniorSDE junior = new JuniorSDE("Alice", 1000.0, 200);
        SDE sde = new SDE("Bob", 1200.0, 150, 2);
        SeniorSDE senior = new SeniorSDE("Charlie", 1500.0, 20);

        department.hire(junior, 2);
        department.hire(sde, 2);
        department.hire(senior, 2);

        department.giveOutBonus();

//        System.out.println(junior.getBonus());
//        System.out.println(sde.getBonus());
//        System.out.println(senior.getBonus());

        double threshold = sde.getBonus() + 1;
        department.layoff(threshold);

        Iterator<Engineer> iterator = department.iterator();
        assertTrue(iterator.hasNext());
        Engineer remainingEngineer = iterator.next();

        assertEquals("Charlie", remainingEngineer.getName());
        System.out.println();
        assertFalse(iterator.hasNext());
    }
}
