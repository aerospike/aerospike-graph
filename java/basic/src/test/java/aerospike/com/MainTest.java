import aerospike.com.Main;
import org.junit.jupiter.api.Test;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;

import static org.junit.jupiter.api.Assertions.assertTrue;

public class MainTest {

    @Test
    public void testFullAppFlow() throws Exception {
        final ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        final PrintStream originalOut = System.out;
        System.setOut(new PrintStream(outputStream));

        Main.main(new String[]{});

        System.setOut(originalOut);
        final String output = outputStream.toString();

        assertTrue(output.contains("Connected to Aerospike Graph Service; Adding Data..."));
        assertTrue(output.contains("Data written successfully..."));
        assertTrue(output.contains("QUERY 1: Transactions initiated by Alice:"));
        assertTrue(output.contains("Dropping Dataset."));
        assertTrue(output.contains("Closing Connection..."));
    }
} 