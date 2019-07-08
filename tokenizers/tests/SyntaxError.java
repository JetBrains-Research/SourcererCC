import java.util.Arrays;

public class Main {
    public static void main(String[] args) {
        String[] strings = Arrays.stream(new String[]{"ab", "bd", "ce"}).toArray(String[]::new);
        for (String str : strings)
            System.out.println(str);
    }
}