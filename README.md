# SpanningTreeProtocol

The purpose of this project is to give users an overview of how do switches work in a local area network.

There are three components in this project.
1. The ./wires executable. This simulates "wires" that can be connected by hosts to transfer packets.
2. The ./bridge executable. This simulates a network switch with spanning tree protocol.
3. The ./host executable. This simulates a simple client that connects to a bridge and just sends and receives simple packets. It is also possible to use other software as clients to connect to a bridge.

To begin the simulation:
1. run the ./wires executable on command line, with an option of giving the number of "wires" it would simulate (the default is 10). Each wire has its own number starting from 0.
2. run the ./bridge executable on command line by giving a MAC address and a set of port numbers that this bridge would have. Each port number correspondings to a wire number. There can be multiple running instances of this process.
3. run the ./host executable on command line by giving a MAC address this client would have, a MAC address of the other client which this client would be connecting to, and a wire number this client would be on. There can be also multiple running instances of this process.
