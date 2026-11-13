import SwiftUI

struct ToDoList: View {
    var body: some View {
        VStack(spacing: 20) {
            Text("To-Do List")
                .font(.largeTitle)
                .fontWeight(.bold)

            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Tasks")
                        .font(.subheadline)
                        .foregroundColor(.blue)

                    List {
                        ForEach(1...10) { index in
                            HStack {
                                Text("Task \(index)")
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                                
                                Spacer()
                                
                                Image(systemName: "checkmark.circle")
                                    .foregroundColor(.green)
                            }
                        }
                    }
                }

                Spacer()

                Button(action: {}) {
                    Text("Add Task")
                        .font(.caption)
                        .foregroundColor(.blue)
                }
            }
        }
    }
}