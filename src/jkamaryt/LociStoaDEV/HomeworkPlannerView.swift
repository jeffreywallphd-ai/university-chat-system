import SwiftUI

struct HomeworkPlannerView: View {
    var body: some View {
        VStack(spacing: 20) {
            Text("Homework Planner")
                .font(.largeTitle)
                .fontWeight(.bold)

            HStack(spacing: 12) {
                Text("Homework Tracker")
                    .font(.subheadline)
                    .foregroundColor(.blue)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Track your assignments and deadlines")
                        .font(.subheadline)
                        .foregroundColor(.secondary)

                    List {
                        ForEach(1...10) { index in
                            HStack {
                                Text("Assignment \(index)")
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                                
                                Text("Due: TBD")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
            }
        }
    }
}
