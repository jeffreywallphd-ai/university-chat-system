import SwiftUI

struct CommonLinksView: View {
    var body: some View {
        VStack(spacing: 20) {
            Text("Quick Links")
                .font(.headline)
                .foregroundColor(.blue)

            HStack(spacing: 12) {
                Text("Official Site")
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                Text("News")
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                Text("Events")
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                Text("Library")
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                Text("Career Fair")
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                Spacer()

                Button(action: {}) {
                    Text("More Links")
                        .font(.caption)
                        .foregroundColor(.blue)
                }
            }
        }
    }
}
