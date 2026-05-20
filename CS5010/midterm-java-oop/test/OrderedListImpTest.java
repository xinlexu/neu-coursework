import org.junit.Before;
import org.junit.Test;
import java.util.function.Predicate;
import static org.junit.Assert.*;

public class OrderedListImpTest {
    private OrderedListImp<Integer> list;

    @Before
    public void setUp() {
        list = new OrderedListImp<>();
    }

    @Test
    public void testAdd() {
        list.add(5);
        list.add(3);
        list.add(8);
        list.add(1);

        String expected = "1 3 5 8";
        assertEquals("testAdd failed", expected, list.toString());
    }

    @Test
    public void testGet() {
        list.add(10);
        list.add(20);
        list.add(30);

        assertEquals("testGet failed for valid index", Integer.valueOf(20), list.get(1));

        try {
            list.get(5);
            fail("Expected IndexOutOfBoundsException for invalid index");
        } catch (IndexOutOfBoundsException e) {
            //PASS
        }
    }

    @Test
    public void testSize() {
        assertEquals("testSize failed for initial size", 0, list.size());

        list.add(10);
        list.add(20);
        assertEquals("testSize failed after adding elements", 2, list.size());
    }

    @Test
    public void testSubList() {
        list.add(5);
        list.add(10);
        list.add(15);
        list.add(20);

        Predicate<Integer> pred = x -> x > 10;
        OrderedList<Integer> subList = list.subList(pred);
        String expected = "15 20";

        assertEquals("testSubList failed", expected, subList.toString());
    }

    @Test
    public void testToString() {
        list.add(3);
        list.add(1);
        list.add(4);

        String expected = "1 3 4";
        assertEquals("testToString failed", expected, list.toString());
    }
}
