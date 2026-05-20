import java.util.Iterator;
import java.util.function.Predicate;

public class OrderedListImp<E extends Comparable<E>> implements OrderedList<E>, Iterable<E> {
    private Node<E> head;
    private int size;

    private static class Node<E> {
        E data;
        Node<E> next;

        Node(E data) {
            this.data = data;
            this.next = null;
        }
    }

    public OrderedListImp() {
        head = null;
        size = 0;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        Node<E> current = head;
        while (current != null) {
            sb.append(current.data);
            if (current.next != null) {
                sb.append(" ");
            }
            current = current.next;
        }
        return sb.toString();
    }

    @Override
    public void add(E value) {
        Node<E> newNode = new Node<>(value);
        if (head == null || value.compareTo(head.data) < 0) {
            newNode.next = head;
            head = newNode;
        } else {
            Node<E> current = head;
            while (current.next != null && value.compareTo(current.next.data) > 0) {
                current = current.next;
            }
            newNode.next = current.next;
            current.next = newNode;
        }
        size++;
    }

    @Override
    public E get(int index) {
        if (index < 0 || index >= size) {
            throw new IndexOutOfBoundsException("Index out of range");
        }
        Node<E> current = head;
        for (int i = 0; i < index; i++) {
            current = current.next;
        }
        return current.data;
    }

    @Override
    public int size() {
        return size;
    }

    @Override
    public OrderedListImp<E> subList(Predicate<E> predicate) {
        OrderedListImp<E> subList = new OrderedListImp<>();
        Node<E> current = head;
        while (current != null) {
            if (predicate.test(current.data)) {
                subList.add(current.data);
            }
            current = current.next;
        }
        return subList;
    }


    @Override
    public Iterator<E> iterator() {
        return new Iterator<E>() {
            private Node<E> current = head;

            @Override
            public boolean hasNext() {
                return current != null;
            }

            @Override
            public E next() {
                E data = current.data;
                current = current.next;
                return data;
            }
        };
    }
}
