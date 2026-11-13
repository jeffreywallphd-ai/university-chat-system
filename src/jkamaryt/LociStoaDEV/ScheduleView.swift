import SwiftUI

struct ScheduleView: View {
    var body: some View {
        VStack(spacing: 20) {
            Text("Schedule")
                .font(.largeTitle)
                .fontWeight(.bold)

            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Upcoming Classes")
                        .font(.subheadline)
                        .foregroundColor(.blue)

                    Text("CS 4601: Machine Learning\nCS 4800: Database Systems")
                        .font(.subheadline)
                        .foregroundColor(.secondary)

                    Text("Mon/Wed/Fri 10:30 AM - 12:00 PM")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                Button(action: {}) {
                    Text("Add Class")
                        .font(.caption)
                        .foregroundColor(.blue)
                }
            }
        }
    }
}
