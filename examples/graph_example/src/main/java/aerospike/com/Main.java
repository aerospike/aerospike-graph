package aerospike.com;

import org.apache.tinkerpop.gremlin.structure.Graph;
import org.apache.tinkerpop.gremlin.structure.Vertex;
import org.apache.tinkerpop.gremlin.driver.Cluster;
import org.apache.tinkerpop.gremlin.driver.remote.DriverRemoteConnection;
import org.apache.tinkerpop.gremlin.process.traversal.dsl.graph.GraphTraversalSource;

import static org.apache.tinkerpop.gremlin.process.traversal.AnonymousTraversalSource.traversal;


public class Main {
    private static final String HOST = "172.18.0.3";
    private static final int PORT = 8182;
    private static final Cluster.Builder BUILDER = Cluster.build().addContactPoint(HOST).port(PORT).enableSsl(false);

    public static void main(String[] args) {
        final Cluster cluster = BUILDER.create();
        System.out.println("CONNECTING TO GRAPH");
        final GraphTraversalSource g = traversal().withRemote(DriverRemoteConnection.using(cluster));
        
        System.out.println("ADDING VERTEX:= FOO");
        g.addV("foo")
            .property("company", "aerospike")
            .property("scale","unlimited")
            .iterate();

        System.out.println("READING BACK DATA..");
        Vertex ReadVertex = g.V().has("company","aerospike").next();

        long airportCount = g.V().hasLabel("airport").count().next();
        long flightCount =  g.V().has("code","SFO").outE().count().next();
        System.out.println("DONE!");
    }
}