import SwiftUI

struct CareerFairView: View {
    var body: some View {
        VStack(spacing: 20) {
            Text("Career Fair")
                .font(.largeTitle)
                .fontWeight(.bold)
                .foregroundColor(.blue)

            HStack(spacing: 12) {
                Text("Career Fair")
                    .font(.headline)
                    .foregroundColor(.blue)

                Spacer()

                VStack(alignment: .leading, spacing: 8) {
                    Text("Join us for the Career Fair!")
                        .font(.subheadline)
                        .foregroundColor(.secondary)

                    Button(action: {
                        // Add career fair event
                    }) {
                        Text("Learn More")
                            .font(.caption)
                            .foregroundColor(.blue)
                    }
                }
            }
        }
    }
}
