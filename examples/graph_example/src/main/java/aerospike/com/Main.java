package aerospike.com;

import org.apache.tinkerpop.gremlin.structure.Graph;
import org.apache.tinkerpop.gremlin.structure.Vertex;
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

        g.addV("foo")
            .property("company", "aerospike")
            .property("scale","unlimited")
            .iterate();

        Vertex ReadVertex = g.V().has("company","aerospike").next();

        long airportCount = g.V().hasLabel("airport").count().next();
        long flightCount =  g.V().has("code","SFO").outE().count().next();
    }
}