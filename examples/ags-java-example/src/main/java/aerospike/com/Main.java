package aerospike.com;

import org.apache.tinkerpop.gremlin.structure.Vertex;
import org.apache.tinkerpop.gremlin.structure.Edge;
import org.apache.tinkerpop.gremlin.driver.Cluster;
import org.apache.tinkerpop.gremlin.driver.remote.DriverRemoteConnection;
import org.apache.tinkerpop.gremlin.process.traversal.dsl.graph.GraphTraversalSource;
import static org.apache.tinkerpop.gremlin.process.traversal.AnonymousTraversalSource.traversal;


public class Main {
    private static final String HOST = "localhost"; 
    
    private static final int PORT = 8182;
    private static final Cluster.Builder BUILDER = Cluster.build().addContactPoint(HOST).port(PORT).enableSsl(false);

    public static void main(String[] args) {
        final Cluster cluster = BUILDER.create();
        final GraphTraversalSource g = traversal().withRemote(DriverRemoteConnection.using(cluster));
        
        System.out.println("CONNECTED TO GRAPH, ADDING ELEMENTS");
        // Add 2 vertices and an edge between them with 2 properties each
        Vertex v1 = g.addV("V1")
            .property("vp1", "vpv1")
            .property("vp2", "vpv2")
            .next();

        Vertex v2 = g.addV("V2")
            .property("vp1", "vpv3")
            .property("vp2", "vpv4")
            .next();

        g.addE("connects").from(v1).to(v2)
            .property("ep1", "ev1")
            .property("ep2", "ev2")
            .iterate();

        System.out.println("READING BACK DATA..");
        
        Edge edge =  g.E().hasLabel("connects").next();
        System.out.print("Edge: ");
        System.out.println(edge);
        System.out.print("Out from: ");
        Vertex outV = edge.outVertex();
        System.out.println(outV);
        System.out.print("In to: ");
        Vertex inV = edge.inVertex();
        System.out.println(inV);

        // List properties
        v1 = g.V().hasLabel("V1").next();
        System.out.println(v1 + " Has Properties:");
        v1.properties()
            .forEachRemaining(property -> {
                System.out.println(
                    "--> " + property.key() + " : " + property.value()
                );
            });

        // Clean up
        g.V().drop().iterate();
        System.out.print("DONE, ");
        try {
            System.out.println("CLOSING CONNECT!");
            cluster.close();
        } catch (Exception e) {
            System.err.println("FAILED TO CLOSE!");
        }
    }
}
